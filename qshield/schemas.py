from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


DecisionStatus = Literal[
    "APPROVED",
    "APPROVED_VITAL_POINTS",
    "MANUAL_REVIEW",
    "REJECTED_DUPLICATE",
    "REJECTED_NOT_ENTITLED",
    "HOSPITAL_FRAUD",
]


class PatientIdentity(BaseModel):
    id: str = Field(min_length=1)
    national_id: str = Field(min_length=1)


class ClaimRecord(BaseModel):
    claim_id: str
    procedure_code: str
    doctor_id: str
    justification: str = ""
    department: str = "OUTPATIENT"
    hospital_id: str = ""
    triage_points: int = Field(default=0, ge=0, le=100)
    policy_tier: str = "BASIC"
    requested_items: list[str] = Field(default_factory=list)


class NphiesRequest(BaseModel):
    transaction_id: str
    patient: PatientIdentity
    claim: ClaimRecord


class FlaggedClaim(BaseModel):
    past_claim_id: str
    doctor_id: str
    similarity_score: float
    quantum_similarity: float


class EntitlementFinding(BaseModel):
    procedure_code: str
    name: str
    category: str
    points_required: int
    entitled: bool
    reason: str


class EntitlementResult(BaseModel):
    applies: bool
    status: DecisionStatus
    fraud_score: int
    triage_points: int
    findings: list[EntitlementFinding]
    vital_approved: bool


class AnalysisResult(BaseModel):
    consistency_score: float
    similarity_score: float
    quantum_similarity: float
    is_duplicate_detected: bool
    status: DecisionStatus
    flagged_claims: list[FlaggedClaim]


class DecisionMetrics(BaseModel):
    consistency_score: float
    similarity_score: float
    quantum_similarity: float
    execution_time_ms: float
    engine: str
    triage_points: int = 0
    fraud_score: int = 0
    vital_approved: bool = False


class DecisionPreview(BaseModel):
    transaction_id: str
    claim_id: str
    anonymized_patient_hash: str
    procedure_code: str
    department: str = "OUTPATIENT"
    hospital_id: str = ""
    decision: DecisionStatus
    metrics: DecisionMetrics
    warnings: list[FlaggedClaim]
    entitlement_findings: list[EntitlementFinding] = Field(default_factory=list)


class MiddlewareResponse(BaseModel):
    status_code: int
    encrypted_payload: str
    decrypted_preview_for_demo: DecisionPreview


class ClaimHistoryItem(BaseModel):
    claim_id: str
    transaction_id: str
    anonymized_patient_hash: str
    procedure_code: str
    doctor_id: str
    decision: str
    consistency_score: float
    similarity_score: float
    quantum_similarity: float
    execution_time_ms: float
    created_at: str
    justification: str = ""
    department: str = "OUTPATIENT"
    hospital_id: str = ""
    triage_points: int = 0
    fraud_score: int = 0


class DashboardStats(BaseModel):
    total_claims: int
    approved: int
    rejected: int
    review: int
    hospital_fraud: int
    avg_execution_time_ms: float
    duplicate_rate: float


class AuditEvent(BaseModel):
    id: int
    event_type: str
    transaction_id: Optional[str]
    detail: dict[str, Any]
    created_at: str
