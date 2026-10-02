from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from qshield.config import settings
from qshield.schemas import AuditEvent, ClaimHistoryItem, DashboardStats
from qshield.security import HIPAASecurityEngine


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ClaimStore:
    def __init__(self, path: Path | None = None, security: HIPAASecurityEngine | None = None) -> None:
        self.path = path or settings.database_path
        self.security = security or HIPAASecurityEngine()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS claims (
                    claim_id TEXT PRIMARY KEY,
                    transaction_id TEXT NOT NULL,
                    anonymized_patient_hash TEXT NOT NULL,
                    procedure_code TEXT NOT NULL,
                    doctor_id TEXT NOT NULL,
                    justification_encrypted TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    consistency_score REAL NOT NULL,
                    similarity_score REAL NOT NULL,
                    quantum_similarity REAL NOT NULL,
                    execution_time_ms REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    transaction_id TEXT,
                    detail_encrypted TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_claims_patient
                    ON claims(anonymized_patient_hash, procedure_code);
                """
            )
            self._ensure_column(conn, "claims", "department", "TEXT NOT NULL DEFAULT 'OUTPATIENT'")
            self._ensure_column(conn, "claims", "hospital_id", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "claims", "triage_points", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(conn, "claims", "fraud_score", "INTEGER NOT NULL DEFAULT 0")

    @staticmethod
    def _ensure_column(conn: sqlite3.Connection, table: str, name: str, ddl: str) -> None:
        columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if name not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")

    def patient_history(self, anonymized_patient_hash: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT claim_id, procedure_code, doctor_id, justification_encrypted
                FROM claims
                WHERE anonymized_patient_hash = ?
                ORDER BY created_at ASC
                """,
                (anonymized_patient_hash,),
            ).fetchall()

        history: list[dict[str, Any]] = []
        for row in rows:
            justification = self.security.decrypt_payload(row["justification_encrypted"])
            history.append(
                {
                    "claim_id": row["claim_id"],
                    "procedure_code": row["procedure_code"],
                    "doctor_id": row["doctor_id"],
                    "justification": justification if isinstance(justification, str) else str(justification),
                }
            )
        return history

    def save_claim(
        self,
        *,
        claim_id: str,
        transaction_id: str,
        anonymized_patient_hash: str,
        procedure_code: str,
        doctor_id: str,
        justification: str,
        decision: str,
        consistency_score: float,
        similarity_score: float,
        quantum_similarity: float,
        execution_time_ms: float,
        department: str = "OUTPATIENT",
        hospital_id: str = "",
        triage_points: int = 0,
        fraud_score: int = 0,
    ) -> None:
        encrypted = self.security.encrypt_payload(justification)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO claims (
                    claim_id, transaction_id, anonymized_patient_hash, procedure_code,
                    doctor_id, justification_encrypted, decision, consistency_score,
                    similarity_score, quantum_similarity, execution_time_ms, created_at,
                    department, hospital_id, triage_points, fraud_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim_id,
                    transaction_id,
                    anonymized_patient_hash,
                    procedure_code,
                    doctor_id,
                    encrypted,
                    decision,
                    consistency_score,
                    similarity_score,
                    quantum_similarity,
                    execution_time_ms,
                    utc_now(),
                    department,
                    hospital_id,
                    triage_points,
                    fraud_score,
                ),
            )

    def list_claims(self, limit: int = 50) -> list[ClaimHistoryItem]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM claims
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        items: list[ClaimHistoryItem] = []
        for row in rows:
            justification = self.security.decrypt_payload(row["justification_encrypted"])
            items.append(
                ClaimHistoryItem(
                    claim_id=row["claim_id"],
                    transaction_id=row["transaction_id"],
                    anonymized_patient_hash=row["anonymized_patient_hash"],
                    procedure_code=row["procedure_code"],
                    doctor_id=row["doctor_id"],
                    decision=row["decision"],
                    consistency_score=row["consistency_score"],
                    similarity_score=row["similarity_score"],
                    quantum_similarity=row["quantum_similarity"],
                    execution_time_ms=row["execution_time_ms"],
                    created_at=row["created_at"],
                    justification=justification if isinstance(justification, str) else "",
                    department=row["department"] if "department" in row.keys() else "OUTPATIENT",
                    hospital_id=row["hospital_id"] if "hospital_id" in row.keys() else "",
                    triage_points=int(row["triage_points"] or 0) if "triage_points" in row.keys() else 0,
                    fraud_score=int(row["fraud_score"] or 0) if "fraud_score" in row.keys() else 0,
                )
            )
        return items

    def stats(self) -> DashboardStats:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_claims,
                    SUM(CASE WHEN decision IN ('APPROVED', 'APPROVED_VITAL_POINTS') THEN 1 ELSE 0 END) AS approved,
                    SUM(CASE WHEN decision IN ('REJECTED_DUPLICATE', 'REJECTED_NOT_ENTITLED') THEN 1 ELSE 0 END) AS rejected,
                    SUM(CASE WHEN decision = 'MANUAL_REVIEW' THEN 1 ELSE 0 END) AS review,
                    SUM(CASE WHEN decision = 'HOSPITAL_FRAUD' THEN 1 ELSE 0 END) AS hospital_fraud,
                    AVG(execution_time_ms) AS avg_execution_time_ms
                FROM claims
                """
            ).fetchone()

        total = int(row["total_claims"] or 0)
        rejected = int(row["rejected"] or 0)
        fraud = int(row["hospital_fraud"] or 0)
        return DashboardStats(
            total_claims=total,
            approved=int(row["approved"] or 0),
            rejected=rejected,
            review=int(row["review"] or 0),
            hospital_fraud=fraud,
            avg_execution_time_ms=round(float(row["avg_execution_time_ms"] or 0.0), 2),
            duplicate_rate=round((rejected / total) if total else 0.0, 2),
        )

    def log_audit(self, event_type: str, transaction_id: Optional[str], detail: dict[str, Any]) -> None:
        encrypted = self.security.encrypt_payload(detail)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_log (event_type, transaction_id, detail_encrypted, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (event_type, transaction_id, encrypted, utc_now()),
            )

    def list_audit(self, limit: int = 40) -> list[AuditEvent]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, event_type, transaction_id, detail_encrypted, created_at
                FROM audit_log
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        events: list[AuditEvent] = []
        for row in rows:
            detail = self.security.decrypt_payload(row["detail_encrypted"])
            events.append(
                AuditEvent(
                    id=row["id"],
                    event_type=row["event_type"],
                    transaction_id=row["transaction_id"],
                    detail=detail if isinstance(detail, dict) else {"raw": detail},
                    created_at=row["created_at"],
                )
            )
        return events

    def reset(self) -> None:
        with self.connect() as conn:
            conn.executescript("DELETE FROM claims; DELETE FROM audit_log;")
