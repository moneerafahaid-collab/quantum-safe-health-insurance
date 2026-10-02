# Quantum-Safe Health Insurance

وسيط تأمين صحي يربط منصة نفيس بمحرك كشف تكرار المطالبات، مع تعمية هوية المريض وتشفير الحمولة قبل إرسال القرار لشبكة التأمين.

This is a working demo of the architecture in the original prototype: HIPAA-style de-identification, a QGNN consistency engine, and NPHIES middleware.

## What it does

1. **Security layer** — HMAC-SHA256 anonymizes patient + national ID. Fernet (AES) encrypts payloads in transit and medical text at rest.
2. **QGNN engine** — turns the medical justification into a stable embedding, then scores Jaccard + cosine similarity against the same patient's prior procedures.
3. **NPHIES middleware** — accepts a claim JSON, loads encrypted history, decides approval / review / rejection, and returns an encrypted response.
4. **ER hospital fraud** — emergency claims are checked for items the patient is not entitled to. Vital operations (CPR, intubation, hemorrhage control) are approved on triage points alone.
5. **Ops dashboard** — Arabic RTL console to submit demo claims, inspect scores, and read the audit trail.

National IDs are never stored. Demo preview JSON is returned only so the dashboard can show a decision.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m qshield demo
python -m qshield serve
```

Open [http://127.0.0.1:8080](http://127.0.0.1:8080). The first tab is a committee briefing for the simulated NPHIES system.

| Command | Purpose |
| --- | --- |
| `python -m qshield demo` | Same duplicate MRI justification as the original script |
| `python -m qshield seed` | Reset SQLite history to the demo patient |
| `python -m qshield serve` | API + dashboard on port 8080 |
| `pytest` | Engine, encryption, and API tests |

## Claim payload

```json
{
  "transaction_id": "NPHIES-TXN-2026-08923",
  "patient": { "id": "PAT-8812", "national_id": "1098765432" },
  "claim": {
    "claim_id": "CLM-2099",
    "procedure_code": "MRI-LUMBAR-01",
    "doctor_id": "DOC-404",
    "justification": "المريض يعاني من ألام حادة في الظهر..."
  }
}
```

`POST /api/nphies/claims` processes that payload. Copy-pasted justifications for the same procedure are rejected; a new procedure on the same patient is approved.

## Note

This is an architecture demo, not a certified HIPAA or NPHIES production integration. Change `QSHIELD_IDENTITY_SALT` before any real data is used.
