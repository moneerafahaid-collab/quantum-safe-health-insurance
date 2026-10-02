# Quantum-Safe Health Insurance

وسيط تأمين صحي محاكي يُربط بشبكة IBM Quantum لإعطاء نتائج كوانتية وتشغيل تجربة الاختبار على مطالبات نفيس، مع تعمية هوية المريض وتشفير الحمولة قبل إرسال القرار لشبكة التأمين.

This simulated system connects to the IBM Quantum Network to produce quantum scoring results and run test experiments, then applies HIPAA-style de-identification and NPHIES middleware.

## What it does

1. **Security layer** — HMAC-SHA256 anonymizes patient + national ID. Fernet (AES) encrypts payloads in transit and medical text at rest.
2. **IBM Quantum / QGNN** — the claim justification is scored through a quantum test path linked to the IBM Quantum Network, then compared with the patient's prior procedures.
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

The live server is published from this same GitHub repo via **Actions → Publish server from GitHub**:
https://github.com/moneerafahaid-collab/quantum-safe-health-insurance/actions/workflows/publish-server.yml

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/moneerafahaid-collab/quantum-safe-health-insurance)

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
