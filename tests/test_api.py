from fastapi.testclient import TestClient

from qshield.api import create_app
from qshield.seed import DEMO_DUPLICATE_REQUEST, seed_demo_data
from qshield.storage import ClaimStore


def test_process_duplicate_claim_via_api(tmp_path) -> None:
    store = ClaimStore(path=tmp_path / "api.db")
    seed_demo_data(store)
    client = TestClient(create_app(store))

    response = client.post("/api/nphies/claims", json=DEMO_DUPLICATE_REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert body["status_code"] == 200
    assert body["decrypted_preview_for_demo"]["decision"] == "REJECTED_DUPLICATE"
    assert body["encrypted_payload"]


def test_health_and_dashboard(tmp_path) -> None:
    store = ClaimStore(path=tmp_path / "api.db")
    seed_demo_data(store)
    client = TestClient(create_app(store))
    assert client.get("/api/health").json()["status"] == "ok"
    page = client.get("/")
    assert page.status_code == 200
    assert "Quantum-Safe Health Insurance" in page.text
