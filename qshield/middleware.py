from __future__ import annotations

import time
from typing import Any, Optional

from qshield import ENGINE_NAME
from qshield.engine import QGNNInferenceEngine
from qshield.entitlement import HospitalERFraudEngine
from qshield.schemas import DecisionMetrics, DecisionPreview, MiddlewareResponse, NphiesRequest
from qshield.security import HIPAASecurityEngine
from qshield.storage import ClaimStore


class QShieldNphiesMiddleware:
    """الربط المباشر كطبقة وسيطة بين منصة نفيس وشبكات التأمين."""

    def __init__(
        self,
        security: HIPAASecurityEngine | None = None,
        qgnn: QGNNInferenceEngine | None = None,
        store: ClaimStore | None = None,
    ) -> None:
        self.security = security or HIPAASecurityEngine()
        self.qgnn = qgnn or QGNNInferenceEngine()
        self.er_fraud = HospitalERFraudEngine()
        self.store = store or ClaimStore(security=self.security)

    def process_nphies_request(
        self,
        nphies_payload: NphiesRequest | dict[str, Any],
        patient_history_db: Optional[list[dict[str, Any]]] = None,
    ) -> MiddlewareResponse:
        request = (
            nphies_payload
            if isinstance(nphies_payload, NphiesRequest)
            else NphiesRequest.model_validate(nphies_payload)
        )
        start_time = time.perf_counter()

        hashed_patient_id = self.security.anonymize_patient_data(
            request.patient.id,
            request.patient.national_id,
        )

        history = patient_history_db
        if history is None:
            history = self.store.patient_history(hashed_patient_id)

        analysis = self.qgnn.evaluate_claim_consistency(request.claim, history)
        entitlement = self.er_fraud.evaluate(request.claim)
        decision = self._final_decision(entitlement.status if entitlement.applies else None, analysis.status)
        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        preview = DecisionPreview(
            transaction_id=request.transaction_id,
            claim_id=request.claim.claim_id,
            anonymized_patient_hash=hashed_patient_id,
            procedure_code=request.claim.procedure_code,
            department=request.claim.department,
            hospital_id=request.claim.hospital_id,
            decision=decision,
            metrics=DecisionMetrics(
                consistency_score=analysis.consistency_score,
                similarity_score=analysis.similarity_score,
                quantum_similarity=analysis.quantum_similarity,
                execution_time_ms=execution_time_ms,
                engine=ENGINE_NAME,
                triage_points=request.claim.triage_points,
                fraud_score=entitlement.fraud_score,
                vital_approved=entitlement.vital_approved,
            ),
            warnings=analysis.flagged_claims,
            entitlement_findings=entitlement.findings,
        )

        self.store.save_claim(
            claim_id=request.claim.claim_id,
            transaction_id=request.transaction_id,
            anonymized_patient_hash=hashed_patient_id,
            procedure_code=request.claim.procedure_code,
            doctor_id=request.claim.doctor_id,
            justification=request.claim.justification,
            decision=decision,
            consistency_score=analysis.consistency_score,
            similarity_score=analysis.similarity_score,
            quantum_similarity=analysis.quantum_similarity,
            execution_time_ms=execution_time_ms,
            department=request.claim.department,
            hospital_id=request.claim.hospital_id,
            triage_points=request.claim.triage_points,
            fraud_score=entitlement.fraud_score,
        )
        self.store.log_audit(
            event_type="NPHIES_CLAIM_PROCESSED",
            transaction_id=request.transaction_id,
            detail={
                "claim_id": request.claim.claim_id,
                "decision": decision,
                "anonymized_patient_hash": hashed_patient_id,
                "procedure_code": request.claim.procedure_code,
                "department": request.claim.department,
                "fraud_score": entitlement.fraud_score,
                "flagged_count": len(analysis.flagged_claims),
            },
        )

        encrypted_response = self.security.encrypt_payload(preview.model_dump())
        return MiddlewareResponse(
            status_code=200,
            encrypted_payload=encrypted_response,
            decrypted_preview_for_demo=preview,
        )

    @staticmethod
    def _final_decision(entitlement_status: str | None, qgnn_status: str) -> str:
        if entitlement_status in {"HOSPITAL_FRAUD", "REJECTED_NOT_ENTITLED"}:
            return entitlement_status
        if entitlement_status == "APPROVED_VITAL_POINTS":
            return "APPROVED_VITAL_POINTS"
        if entitlement_status == "MANUAL_REVIEW" and qgnn_status != "REJECTED_DUPLICATE":
            return "MANUAL_REVIEW"
        return qgnn_status
