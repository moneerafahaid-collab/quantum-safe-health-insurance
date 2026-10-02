from __future__ import annotations

from qshield.middleware import QShieldNphiesMiddleware
from qshield.security import HIPAASecurityEngine
from qshield.storage import ClaimStore


HISTORY_JUSTIFICATION = (
    "المريض يعاني من ألام حادة في الظهر وتم إعطاء علاج مسكن ولم يتحسن ويرغب في عمل أشعة"
)

DEMO_HISTORY_CLAIM = {
    "claim_id": "CLM-1001",
    "transaction_id": "NPHIES-TXN-2025-SEED",
    "patient_id": "PAT-8812",
    "national_id": "1098765432",
    "procedure_code": "MRI-LUMBAR-01",
    "doctor_id": "DOC-99",
    "justification": HISTORY_JUSTIFICATION,
}

DEMO_DUPLICATE_REQUEST = {
    "transaction_id": "NPHIES-TXN-2026-08923",
    "patient": {"id": "PAT-8812", "national_id": "1098765432"},
    "claim": {
        "claim_id": "CLM-2099",
        "procedure_code": "MRI-LUMBAR-01",
        "doctor_id": "DOC-404",
        "justification": HISTORY_JUSTIFICATION,
    },
}

DEMO_UNIQUE_REQUEST = {
    "transaction_id": "NPHIES-TXN-2026-09001",
    "patient": {"id": "PAT-8812", "national_id": "1098765432"},
    "claim": {
        "claim_id": "CLM-3100",
        "procedure_code": "LAB-CBC-01",
        "doctor_id": "DOC-12",
        "justification": "تحليل دم روتيني لمتابعة فقر الدم بعد بدء الحديد الفموي لمدة ثمانية أسابيع.",
    },
}

DEMO_REVIEW_REQUEST = {
    "transaction_id": "NPHIES-TXN-2026-09077",
    "patient": {"id": "PAT-8812", "national_id": "1098765432"},
    "claim": {
        "claim_id": "CLM-3188",
        "procedure_code": "MRI-LUMBAR-01",
        "doctor_id": "DOC-77",
        "justification": "المريض يعاني من آلام في الظهر بعد علاج مسكن ويحتاج إعادة تقييم بالأشعة.",
    },
}

DEMO_ER_VITAL_REQUEST = {
    "transaction_id": "NPHIES-TXN-2026-ER-1001",
    "patient": {"id": "PAT-8812", "national_id": "1098765432"},
    "claim": {
        "claim_id": "CLM-ER-4401",
        "procedure_code": "ER-CPR-01",
        "doctor_id": "DOC-ER-7",
        "department": "ER",
        "hospital_id": "HOSP-HAIL-01",
        "triage_points": 82,
        "policy_tier": "BASIC",
        "requested_items": [],
        "justification": "توقف قلب في قسم الطوارئ واستدعي الإنعاش فوراً.",
    },
}

DEMO_ER_FRAUD_REQUEST = {
    "transaction_id": "NPHIES-TXN-2026-ER-2088",
    "patient": {"id": "PAT-8812", "national_id": "1098765432"},
    "claim": {
        "claim_id": "CLM-ER-4499",
        "procedure_code": "ER-STABILIZE-01",
        "doctor_id": "DOC-ER-19",
        "department": "ER",
        "hospital_id": "HOSP-HAIL-01",
        "triage_points": 18,
        "policy_tier": "BASIC",
        "requested_items": ["MRI-LUMBAR-01", "PRIVATE-SUITE-01", "COSMETIC-FILLER-01"],
        "justification": "مراجع طوارئ بشكوى خفيفة وتم طلب رنين وجناح خاص وتجميل دون أحقية.",
    },
}

DEMO_ER_UNENTITLED_REQUEST = {
    "transaction_id": "NPHIES-TXN-2026-ER-3012",
    "patient": {"id": "PAT-8812", "national_id": "1098765432"},
    "claim": {
        "claim_id": "CLM-ER-4510",
        "procedure_code": "MRI-LUMBAR-01",
        "doctor_id": "DOC-ER-19",
        "department": "ER",
        "hospital_id": "HOSP-HAIL-01",
        "triage_points": 22,
        "policy_tier": "BASIC",
        "requested_items": [],
        "justification": "طلب رنين أسفل الظهر من الطوارئ دون أن يكون مشمولاً في الوثيقة.",
    },
}


def seed_demo_data(store: ClaimStore | None = None) -> ClaimStore:
    security = HIPAASecurityEngine()
    store = store or ClaimStore(security=security)
    store.reset()

    hashed = security.anonymize_patient_data(
        DEMO_HISTORY_CLAIM["patient_id"],
        DEMO_HISTORY_CLAIM["national_id"],
    )
    store.save_claim(
        claim_id=DEMO_HISTORY_CLAIM["claim_id"],
        transaction_id=DEMO_HISTORY_CLAIM["transaction_id"],
        anonymized_patient_hash=hashed,
        procedure_code=DEMO_HISTORY_CLAIM["procedure_code"],
        doctor_id=DEMO_HISTORY_CLAIM["doctor_id"],
        justification=DEMO_HISTORY_CLAIM["justification"],
        decision="APPROVED",
        consistency_score=1.0,
        similarity_score=0.0,
        quantum_similarity=0.0,
        execution_time_ms=1.2,
    )
    store.log_audit(
        event_type="DEMO_SEEDED",
        transaction_id=DEMO_HISTORY_CLAIM["transaction_id"],
        detail={"claim_id": DEMO_HISTORY_CLAIM["claim_id"], "decision": "APPROVED"},
    )
    return store


def run_console_demo() -> dict:
    store = seed_demo_data()
    middleware = QShieldNphiesMiddleware(store=store)
    result = middleware.process_nphies_request(DEMO_DUPLICATE_REQUEST)
    return result.model_dump()
