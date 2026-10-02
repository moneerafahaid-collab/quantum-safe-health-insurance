from qshield.entitlement import HospitalERFraudEngine
from qshield.middleware import QShieldNphiesMiddleware
from qshield.seed import DEMO_ER_FRAUD_REQUEST, DEMO_ER_UNENTITLED_REQUEST, DEMO_ER_VITAL_REQUEST, seed_demo_data
from qshield.storage import ClaimStore


def test_er_vital_procedure_approved_by_points_only() -> None:
    result = HospitalERFraudEngine().evaluate(DEMO_ER_VITAL_REQUEST["claim"])
    assert result.applies is True
    assert result.status == "APPROVED_VITAL_POINTS"
    assert result.vital_approved is True
    assert result.findings[0].entitled is True


def test_er_luxury_stuffing_is_hospital_fraud() -> None:
    result = HospitalERFraudEngine().evaluate(DEMO_ER_FRAUD_REQUEST["claim"])
    assert result.status == "HOSPITAL_FRAUD"
    assert result.fraud_score >= 50
    denied = [item.procedure_code for item in result.findings if not item.entitled]
    assert "PRIVATE-SUITE-01" in denied
    assert "COSMETIC-FILLER-01" in denied


def test_er_mri_without_entitlement_is_rejected() -> None:
    result = HospitalERFraudEngine().evaluate(DEMO_ER_UNENTITLED_REQUEST["claim"])
    assert result.status == "REJECTED_NOT_ENTITLED"


def test_outpatient_skips_er_entitlement() -> None:
    result = HospitalERFraudEngine().evaluate(
        {
            "claim_id": "CLM-X",
            "procedure_code": "MRI-LUMBAR-01",
            "doctor_id": "DOC-1",
            "department": "OUTPATIENT",
            "justification": "عيادة",
        }
    )
    assert result.applies is False


def test_middleware_er_fraud_and_vital(tmp_path) -> None:
    store = ClaimStore(path=tmp_path / "er.db")
    seed_demo_data(store)
    middleware = QShieldNphiesMiddleware(store=store)
    fraud = middleware.process_nphies_request(DEMO_ER_FRAUD_REQUEST).decrypted_preview_for_demo
    vital = middleware.process_nphies_request(DEMO_ER_VITAL_REQUEST).decrypted_preview_for_demo
    assert fraud.decision == "HOSPITAL_FRAUD"
    assert vital.decision == "APPROVED_VITAL_POINTS"
    assert vital.metrics.triage_points == 82
