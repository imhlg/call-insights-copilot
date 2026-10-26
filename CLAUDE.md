# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal learning workspace for the **call-insights-copilot** project (project 1 of **FORGE v6**): Python LLM exercises in a contact-center / telecom support scenario. Light tasks use local Ollama; heavy tasks use MiMo Pro. Scripts are standalone lessons, not a packaged app. Shared code lives in `src/common/`; `tests/` has mocked routing tests and will hold evals from Week 3.

**Learning plan:** `docs/FORGE v6_ MAKER, FIELD and SHARPEN (19 Oct 2026 to 28 Feb 2027).html` (canonical). Summary: `docs/FORGE v6_ ... .md`. Legacy plans are in `docs/archive/`.

**Phases:** MAKER (19 Oct – 27 Dec 2026, AI PM ready) → FIELD (28 Dec – 28 Feb 2027, FDE ready) → SHARPEN (Mar 2027+, revision only). Weeks 1–2 are marked done in the plan; **Week 3** (19 Oct) is Pydantic, one-tool agent, eval v0, public repo by **25 Oct**.

## Setup and running

```bash
source venv/bin/activate          # ./venv (.gitignore also covers .venv)
pip install -r requirements.txt
python src/1stWeek-refund-checker/week1-Day1.py
```

Install `requirements-dev.txt` when running tests with `python -m pytest`.

Use `.env.example` as a template and merge its values into `.env` (gitignored). Ollama runs locally and needs no secret; heavy tasks need `MIMO_API_KEY`. `src/common/config.py` loads these settings.

`src/common/config.py` validates provider settings. `src/common/model_router.py` selects MiMo Pro for code over 30,000 characters or tasks named `refactor`, `architecture`, or `debug_hard`; other tasks use Ollama. If that Ollama call is still running after 180 seconds, `llm_client` sends the same light task to Claude Haiku 5.5 at low effort (`ANTHROPIC_API_KEY`). `src/common/llm_client.py` calls the provider and returns a typed result. Change `OLLAMA_MODEL` in `.env` to change the local model. Heavy calls stay pinned to MiMo v2.6 Pro.

`7thDay.py` uses `requests` only; `8thDay.py` is keyword FAQ work.

`pyrightconfig.json` sets `extraPaths: ["src/common"]` so shared imports resolve in the IDE.

## Layout

- `src/common/`
  - `config.py` — validated settings and provider URLs.
  - `model_router.py` — `pick_model(task, code)` and provider routing.
  - `llm_client.py` — provider calls and typed `LLMResult` values.
  - `refund_checker.py` — `REFUND_CHECK_SYSTEM`, `flag_refund_promise()`.
- `src/1stWeek-refund-checker/week1-DayN.py` — Days 1–5.
- `src/2ndWeek/` — `6thDay.py`, `7thDay.py`, `8thDay.py` (day numbers continue from week 1).
- `docs/` — FORGE v6 plan, job search tracker.
- `data/` — empty for now.

Filenames use hyphens or leading digits; run as scripts, do not import as modules.

## Structure and conventions

- Add `src/common` to `sys.path` **before** importing shared code:

  ```python
  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))

  from llm_client import llm
  ```

  Route calls by task. The client measures user-message text when `code` is omitted; pass `code=source_code` to select using an explicit source string:
  `llm.complete(task="refactor", code=source_code, max_output_tokens=300, messages=[...])`.

- Keep finished exercises as commented blocks or `"""part 1"""` / `"""Output was- ..."""` notes; usually only the last block runs.
- Refund-checker logic stays in `src/common/refund_checker.py`.
- Pass `task` and, when available, the code being analyzed to `llm.complete`; `pick_model` applies the size and heavy-task rules.
- Read model text from `LLMResult.text`; usage and provider metadata are on the same result.

## Exercises (Weeks 1–2, plan: done)

**Week 1** — catch support-bot replies that promise a refund: API basics → system prompt + regex → JSON + LLM judge → multi-turn tokens → precision/recall test set.

**Week 2**

- **6thDay.py** — local-model JSON triage, validation, retries; `triage` returns `None` if all attempts fail.
- **7thDay.py** — `requests`, `timeout`, `raise_for_status`, `RequestException`.
- **8thDay.py** — keyword FAQ over five synthetic FAQs (`FAQS` dict). Done: strip punctuation, drop `STOP_WORDS`, expand with `SYNONYMS`, score each FAQ by substring match (`score2`). Not built yet: returning a `source` key for citations. Week 4 RAG compares against this baseline.

## FORGE v6 context for this repo

- **Next build (Week 3):** Pydantic output, one-tool agent (e.g. FAQ lookup), eval v0 (40 cases, single `pytest` command), public repo.
- **Other FORGE projects** (separate repos later): contact-center-data, customer-integration-service, collections-recovery-assistant, algo-trading-lab, plus the **FORGE platform** (login, per-user keys, metering, spend caps).
- **Telephony** (~9 h total): concept Week 6; Twilio/Genesys lab Week 14; sandbox SMS Week 15; connector page Week 19.
- **Trading:** backtest and paper only; no broker keys on platform.

When suggesting work, prefer the open week in the FORGE HTML and the **25 Oct** milestone unless the user is explicitly finishing Week 2 code.

## Repo state

- Exercise folders may be untracked until pushed; `.gitignore` covers `venv/`, `.env`, `__pycache__/`.
