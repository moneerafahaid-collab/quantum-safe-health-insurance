from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from qshield import ENGINE_NAME, __version__
from qshield.config import STATIC_DIR, TEMPLATES_DIR
from qshield.middleware import QShieldNphiesMiddleware
from qshield.schemas import NphiesRequest
from qshield.seed import (
    DEMO_DUPLICATE_REQUEST,
    DEMO_ER_FRAUD_REQUEST,
    DEMO_ER_UNENTITLED_REQUEST,
    DEMO_ER_VITAL_REQUEST,
    DEMO_REVIEW_REQUEST,
    DEMO_UNIQUE_REQUEST,
    seed_demo_data,
)
from qshield.storage import ClaimStore


def create_app(store: ClaimStore | None = None) -> FastAPI:
    store = store or ClaimStore()
    middleware = QShieldNphiesMiddleware(store=store)

    app = FastAPI(
        title="Quantum-Safe Health Insurance",
        description="Quantum-safe NPHIES claim consistency engine",
        version=__version__,
    )
    app.state.store = store
    app.state.middleware = middleware

    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "index.html",
            {"engine": ENGINE_NAME, "version": __version__},
        )

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "engine": ENGINE_NAME, "version": __version__}

    @app.get("/api/stats")
    def stats() -> dict:
        return app.state.store.stats().model_dump()

    @app.get("/api/claims")
    def claims(limit: int = 50) -> dict:
        return {"items": [item.model_dump() for item in app.state.store.list_claims(limit)]}

    @app.get("/api/audit")
    def audit(limit: int = 40) -> dict:
        return {"items": [item.model_dump() for item in app.state.store.list_audit(limit)]}

    @app.get("/api/demo-payloads")
    def demo_payloads() -> dict:
        return {
            "duplicate": DEMO_DUPLICATE_REQUEST,
            "unique": DEMO_UNIQUE_REQUEST,
            "review": DEMO_REVIEW_REQUEST,
            "er_vital": DEMO_ER_VITAL_REQUEST,
            "er_fraud": DEMO_ER_FRAUD_REQUEST,
            "er_unentitled": DEMO_ER_UNENTITLED_REQUEST,
        }

    @app.post("/api/nphies/claims")
    def process_claim(payload: NphiesRequest) -> dict:
        try:
            result = app.state.middleware.process_nphies_request(payload)
        except Exception as exc:  # pragma: no cover - defensive API boundary
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return result.model_dump()

    @app.post("/api/demo/reset")
    def reset_demo() -> dict:
        seed_demo_data(app.state.store)
        return {"status": "seeded", "stats": app.state.store.stats().model_dump()}

    return app


app = create_app()
