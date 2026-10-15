# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal learning workspace for working with the Anthropic Python SDK (the Claude API), built around a contact-center / telecom support scenario. Each script is a standalone exercise, not part of a package or application. `data/` and `tests/` are empty, and there is no test suite, linter, or build step.

## Setup and running

```bash
source venv/bin/activate          # the venv is in ./venv (.gitignore also covers .venv)
pip install -r requirements.txt
python src/1stWeek-refund-checker/week1-Day1.py
```

`ANTHROPIC_API_KEY` lives in `.env` (gitignored). `src/common/config.py` loads it with `load_dotenv()`, so scripts that import `config` need no extra setup.

Every script calls the live API when it runs (except `7thDay.py` and `8thDay.py`, which make HTTP requests or do plain string work), so running one costs tokens.

## Layout

- `src/common/`: shared code used across exercises.
  - `config.py` creates the `client` and defines `HK_MODEL` (`claude-haiku-5-5`) and `SONNET_MODEL` (`claude-sonnet-5-5`).
  - `refund_checker.py` holds `REFUND_CHECK_SYSTEM` (the judge prompt) and `flag_refund_promise()` (the regex detector).
- `src/1stWeek-refund-checker/week1-DayN.py`: week 1 lesson files, Days 1 to 5.
- `src/2ndWeek/`: week 2 lesson files, named `6thDay.py`, `7thDay.py`, and `8thDay.py` (the day numbers continue from week 1).
- `docs/`: the 12-week plan (HTML and PDF) and a job search tracker. Not yet committed.
- `data/`, `tests/`: empty.

Filenames contain hyphens or start with digits, so they can't be imported. Run them as scripts.

## Structure and conventions

- Every exercise file adds `src/common` to `sys.path` before importing shared code:
  ```python
  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))

  from config import client, HK_MODEL
  ```
  Copy this header for any new file in `src/1stWeek-refund-checker/` or `src/2ndWeek/`.
- Within a file, earlier exercises are kept as commented-out blocks or bare `"""..."""` strings labelled `part 1`, `part 2`, `bonus`, and so on. Usually only the last block runs. Earlier outputs are pasted into `"""Output was- ..."""` strings as notes. Keep this style: comment out finished exercises instead of deleting them.
- Put refund-checker logic in `src/common/refund_checker.py`, not in individual day files. Day files import it.
- Models: use `HK_MODEL` (haiku) for cheap checks and `SONNET_MODEL` for stronger ones. `temperature` is deprecated on these models (see the Day2 notes). Use system prompts to control output instead.
- Response text is read with `response.content[-1].text` or by filtering for blocks where `block.type == "text"`.

## The exercises

Week 1 builds one idea across the days: catch support-bot replies that promise a refund.
1. **Day 1**: first API calls, token usage, and a system-prompt bonus.
2. **Day 2**: a system prompt forbids refund promises, and `flag_refund_promise` (in `common/`) scans the reply.
3. **Day 3**: structured JSON output (`json.loads` on the reply), plus an LLM-as-judge classifier (`{"promises_money_back": bool}`) compared against the regex.
4. **Day 4**: multi-turn conversation by appending to a `history` list, watching `usage.input_tokens` grow.
5. **Day 5**: a labelled `test_set` of `(sentence, truth)` pairs and a `score()` function that reports caught/false-alarm/missed counts and precision/recall for the regex and the model. Edge cases include conditional promises, paraphrases, negations, and instruction-override attempts.

Week 2:
- **6thDay.py**: support-message triage with a JSON reply, validation checks, and retries when the reply is cut off or invalid. `parse_triage` raises `ValueError` on bad fields so the retry runs; if all attempts fail, `triage` returns `None`.
- **7thDay.py**: HTTP requests with `requests` and error handling.
- **8thDay.py**: a small FAQ answer generator and string cleanup exercise.

## Repo state

- `src/1stWeek-refund-checker/` and `src/2ndWeek/` are untracked and not yet committed.
- The `.gitignore` covers `venv/`, `.venv/`, `.env`, `__pycache__/`, and `.DS_Store`.
- Branch for this work: `cursor/shared-client-config-and-week2`. Main branch: `main`.
