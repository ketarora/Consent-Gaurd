# Consent Guard

Consent Guard is a compliance guardrail for agentic commerce messaging.  
It intercepts agent-to-customer text, flags manipulative dark patterns, and requires human review before release.

Built for Razorpay Buildathon (Agentic Commerce track).

---

## 1) Problem → Business Impact

Agentic commerce systems optimize conversion aggressively. Without language guardrails, agents can drift into manipulative messaging (false urgency, confirm shaming, hidden fees framing, etc.).

For payment platforms and merchants, this can increase:
- refund/dispute risk,
- trust erosion and churn,
- compliance operations overhead.

Consent Guard provides a **fail-closed interception layer** with an auditable decision trail.

---

## 2) Regulatory scope and terminology

This project uses categories aligned to **India’s Central Consumer Protection Authority (CCPA) 2023 dark-pattern guidelines** for commerce messaging checks.

Scope in this prototype:
- false_urgency
- confirm_shaming
- forced_continuity
- drip_pricing
- basket_sneaking

---

## 3) How it plugs into merchant/payment flow

```text
Merchant AI Agent
   -> Consent Guard /api/intercept
      -> prefilter (fast urgency patterns)
      -> allowlist check for real deadlines
      -> LLM classifier for nuanced categories
      -> action: sent | held
      -> audit record (JSONL + SQLite)
   -> if held: human reviewer approves/rejects in dashboard
```

---

## 4) Live demo flow (one-click)

Frontend supports:
- **Run guided demo** (injects a full trace),
- **Simulate 1/2/3** quick messages,
- reviewer controls (Approve / Reject),
- **Export audit (.JSONL)** from backend.

Demo assets for recording are in:
- `/home/runner/work/Consent-Gaurd/Consent-Gaurd/demo/VIDEO_NARRATION_SCRIPT.md`
- `/home/runner/work/Consent-Gaurd/Consent-Gaurd/demo/EXPECTED_OUTCOMES_CHECKLIST.md`

---

## 5) Measured outcomes (current repo artifacts)

Generated artifacts:
- `/home/runner/work/Consent-Gaurd/Consent-Gaurd/eval/results.json`
- `/home/runner/work/Consent-Gaurd/Consent-Gaurd/eval/consent_guard_dataset_cleaned.json`
- `/home/runner/work/Consent-Gaurd/Consent-Gaurd/eval/latency_results.json`

`eval/results.json` includes:
- total/category counts,
- confusion matrix (TP/FP/TN/FN),
- precision/recall/F1/accuracy for deterministic prefilter+allowlist path.

`eval/latency_results.json` includes:
- mean/median/p95/p99/max latency for deterministic path.

---

## 6) Quick start

### Backend (Terminal A)
```bash
cd /home/runner/work/Consent-Gaurd/Consent-Gaurd/backend
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows
# venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

### Frontend (Terminal B)
```bash
cd /home/runner/work/Consent-Gaurd/Consent-Gaurd/frontend
npm install
npm run dev
```

Open:
- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/

---

## 7) Reproducible evaluation commands

From repo root:
```bash
python eval/run_eval.py --input consent_guard_dataset.json --out eval/results.json --clean
python eval/benchmark_latency.py --input consent_guard_dataset.json --out eval/latency_results.json --iterations 20
```

---

## 8) Merchant integration example

Run:
```bash
python scripts/merchant_agent_example.py --base-url http://localhost:8000/api
```

Walkthrough with expected output:
- `/home/runner/work/Consent-Gaurd/Consent-Gaurd/scripts/README.md`

---

## 9) Security and safeguards in this version

- Optional API key auth on intercept endpoint (`CONSENT_GUARD_API_KEY`)
- Basic per-IP rate limit on intercept endpoint (`RATE_LIMIT_MAX_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`)
- Fail-closed classifier behavior (`classifier_error` leads to held action)

---

## 10) Known limitations

- LLM quality metrics are not auto-generated in CI (API-key dependent and cost-limited).
- Rate limiting is in-memory (single-instance demo), not distributed.
- JSONL audit log is append-only by application behavior, not cryptographically tamper-proof.

---

## 11) Production hardening path

1. Distributed rate limiter (Redis) and authenticated service-to-service calls.
2. Signed/tamper-evident audit records and long-term archival.
3. Provider-independent LLM eval harness with scheduled holdout runs.
4. Policy/config management UI for compliance teams.

---

## 12) CI

Workflow: `/home/runner/work/Consent-Gaurd/Consent-Gaurd/.github/workflows/ci.yml`

Runs:
- backend tests,
- deterministic eval script,
- deterministic latency benchmark,
- frontend production build.
