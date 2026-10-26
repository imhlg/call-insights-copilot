# FORGE v6: MAKER, FIELD and SHARPEN

**Source of truth:** `FORGE v6_ MAKER, FIELD and SHARPEN (19 Oct 2026 to 28 Feb 2027).html` (interactive week-by-week view). Older plans live in `docs/archive/`.

## Phases

| Phase | Dates | Goal |
|--------|--------|------|
| **MAKER** | 19 Oct – 27 Dec 2026 | AI PM interview-ready (Track 1) |
| **FIELD** | 28 Dec 2026 – 28 Feb 2027 | FDE-ready; **hard stop 28 Feb** (52 h/week) |
| **SHARPEN** | From 1 Mar 2027 | Revision and exercises only; no new topics |

Weeks **1 and 2** (refund checker, JSON/retries, HTTP, keyword FAQ) are **done**. Calendar **Week 3** starts **19 Oct**.

## Time

- **MAKER:** ~49 h/week (36 technical, 9 product/say, 2 search, 2 admin).
- **FIELD:** 52 h/week (39 technical).
- Catch-up: half-day every other Saturday, only if behind.
- Tools: Cursor for edits; Claude Code CLI on `claude-haiku-5-5` for multi-file builds and test-and-fix loops.

## Five projects + FORGE platform

1. **call-insights-copilot** — refund/disclaimer checks, agents, MCP, evals, PII, red team (this repo’s main thread).
2. **contact-center-data** — extraction, warehouse, quality, mining, ML, Airflow.
3. **customer-integration-service** — FastAPI, webhooks, queues, CRM sandbox, deploy.
4. **collections-recovery-assistant** — propensity, checked messages, payment plans, fairness.
5. **algo-trading-lab** — walk-forward backtest, risk limits in code, LLM trade journal + evals; **paper trading only**.

**FORGE platform** — SaaS-style site: login, per-user API keys, usage metering, spend caps, one page per project; fronts all five.

Synthetic customer data only. Trading uses **public** market data under provider terms; **no real money**, no broker keys on the platform, not investment advice.

## Milestones

| Date | Deliverable |
|------|-------------|
| **25 Oct** | Repo public, eval v0 |
| **8 Nov** | Eval harness, checkpoint round 1 |
| **22 Nov** | Agent + MCP live, checkpoint round 2 |
| **6 Dec** | Postgres and SQL, checkpoint round 3 |
| **27 Dec** | Interview-ready core, Phase 1 exam |
| **31 Jan** | Mid-point exam |
| **28 Feb** | All topics covered, final exam |
| **Mar 2027** | SHARPEN only |

## Week 3 (current MAKER week): 19–25 Oct

- **Build:** Python gate (90 min, no notes); Pydantic structured output; one-tool agent; eval v0 on 40 synthetic cases (precision/recall, one `pytest` command); spec → tests → build → review; secrets check; **repo public**.
- **Track 2:** Linux/shell; networking (DNS, HTTP, TLS, curl); Git; latency concept.
- **Product:** Intro pitch; AXM story; metric tree; RICE; Week 1–2 rescue flashcards (60 min).
- **Added:** CV v1 for AI PM (6 h by 25 Oct); two 30-min no-AI coding drills/week; Anthropic + AWS spending caps.

## Telephony track (added 16 Oct, ~9 technical hours)

| Week | Addition |
|------|-----------|
| **6** | Telephony concept (1 h): PSTN, SIP, IVR, DTMF, recording, streaming; link to U-Assist Genesys delay |
| **14** | Telephony lab (8 h): Twilio voice webhook, TwiML, status callbacks, signature check; Genesys Cloud sandbox data action (Amazon Connect: explain and try only) |
| **15** | Sandbox SMS via Twilio in message checker; learn India DLT rules |
| **19** | Telephony connector page on platform (2 h) |

**Release valve:** At start of Week 19 (8 Feb), optional FIELD extension to **15 Mar** (~78 technical hours) if telephony/platform slips.

## Strands (scope summary)

- **AI core** — prompting, structured output, RAG (recall@k, MRR), evals, agents, MCP, safety, cost, routing, tracing, etc.
- **Backend** — Linux, FastAPI, auth, webhooks, Redis, AWS, Docker, CI with evals, observability.
- **Data** — extraction, DuckDB/dbt, Postgres, SQL, pipelines, A/B.
- **Classic ML** — logistic regression through SHAP, MLflow, drift, fairness.
- **Design / FDE** — drills, FDE pack, prototypes, security questionnaire.
- **PM / Staff TPM** — PRD, metrics, RICE, stories (Siebel, U-Assist, Asurion, AXM, Malayalam).
- **Platform and trading** — metering, caps, kill switch, admin dashboard; backtest + paper trading only.

## Rules (high signal)

- `.env` never committed; monthly Anthropic limit + AWS budget alert by end of Week 3.
- If behind: keep order, hit milestones first; stretch → explain-and-try; use catch-up Saturdays.
- Interview week: drop to 30 technical hours; move rest to catch-up or SHARPEN.
- AI PM and FDE gates are never cut; max 52 h/week.
- Hard monthly budget for platform (hosting, domain, keys) before launch.

## Assessments

- Daily: flashcards + 3 mixed questions.
- Checkpoints: 8 Nov, 22 Nov, 6 Dec (20 questions each).
- Exams: 27 Dec, 31 Jan, 28 Feb — 60 questions + 3-hour prototype; **80% pass**; missed topics repeat next week.
- **28 Feb FDE gate:** five repos + demos, live platform with spend caps, two accounts, CI evals, FDE pack, two timed prototypes, three debug labs &lt;30 min, one mock FDE loop.

## Copilot module map (call-insights-copilot)

| MAKER week | Module |
|------------|--------|
| 1–2 | Summarizer + refund checker; keyword retrieval (`8thDay.py`) |
| 3 | Tool-use agent + eval v0 |
| 4 | RAG + embeddings |
| 5 | Eval harness (80 cases) |
| 6–8 | Agent loop, MCP, safety / red team |
| 9+ | Service, deploy, platform shell (Week 9) |

Week 4 RAG must **compare against Week 2 keyword search** on the same questions.
