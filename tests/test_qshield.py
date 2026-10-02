from __future__ import annotations

from qshield.engine import QGNNInferenceEngine
from qshield.middleware import QShieldNphiesMiddleware
from qshield.security import HIPAASecurityEngine
from qshield.seed import DEMO_DUPLICATE_REQUEST, HISTORY_JUSTIFICATION, seed_demo_data
from qshield.storage import ClaimStore


def test_anonymize_is_deterministic_and_hides_national_id() -> None:
    engine = HIPAASecurityEngine()
    first = engine.anonymize_patient_data("PAT-8812", "1098765432")
    second = engine.anonymize_patient_data("PAT-8812", "1098765432")
    other = engine.anonymize_patient_data("PAT-8812", "1098765433")
    assert first == second
    assert first != other
    assert "1098765432" not in first
    assert len(first) == 64


def test_encrypt_decrypt_roundtrip() -> None:
    engine = HIPAASecurityEngine()
    payload = {"transaction_id": "NPHIES-TXN-1", "decision": "APPROVED"}
    token = engine.encrypt_payload(payload)
    assert token != str(payload)
    assert engine.decrypt_payload(token) == payload


def test_duplicate_justification_is_rejected(tmp_path) -> None:
    store = ClaimStore(path=tmp_path / "test.db")
    seed_demo_data(store)
    middleware = QShieldNphiesMiddleware(store=store)
    result = middleware.process_nphies_request(DEMO_DUPLICATE_REQUEST)
    preview = result.decrypted_preview_for_demo
    assert result.status_code == 200
    assert preview.decision == "REJECTED_DUPLICATE"
    assert preview.warnings
    assert preview.warnings[0].past_claim_id == "CLM-1001"


def test_unique_procedure_is_approved(tmp_path) -> None:
    store = ClaimStore(path=tmp_path / "test.db")
    seed_demo_data(store)
    middleware = QShieldNphiesMiddleware(store=store)
    payload = {
        "transaction_id": "NPHIES-TXN-UNIQUE",
        "patient": {"id": "PAT-8812", "national_id": "1098765432"},
        "claim": {
            "claim_id": "CLM-5001",
            "procedure_code": "CT-CHEST-02",
            "doctor_id": "DOC-12",
            "justification": "اشتباه التهاب رئوي مع سعال مستمر لمدة ثلاثة أسابيع.",
        },
    }
    preview = middleware.process_nphies_request(payload).decrypted_preview_for_demo
    assert preview.decision == "APPROVED"
    assert preview.warnings == []


def test_partial_overlap_goes_to_manual_review() -> None:
    engine = QGNNInferenceEngine(similarity_threshold=0.85, review_threshold=0.60)
    current = {
        "claim_id": "CLM-A",
        "procedure_code": "MRI-LUMBAR-01",
        "doctor_id": "DOC-1",
        "justification": "one two three four five six seven",
    }
    history = [
        {
            "claim_id": "CLM-B",
            "procedure_code": "MRI-LUMBAR-01",
            "doctor_id": "DOC-2",
            "justification": "one two three four five six extra",
        }
    ]
    result = engine.evaluate_claim_consistency(current, history)
    assert result.status == "MANUAL_REVIEW"
    assert result.is_duplicate_detected is False
    assert result.flagged_claims


def test_quantum_embedding_is_stable() -> None:
    engine = QGNNInferenceEngine()
    left = engine.quantum_state_embedding(HISTORY_JUSTIFICATION)
    right = engine.quantum_state_embedding(HISTORY_JUSTIFICATION)
    assert left == right
    assert all(0.0 <= value <= 1.0 for value in left)
