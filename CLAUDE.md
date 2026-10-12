# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal learning workspace for working with the Anthropic Python SDK (the Claude API), built around a contact-center / telecom support scenario. Each script is a standalone exercise, not part of a package or application. `data/`, `docs/`, and `tests/` exist but are currently empty, and there is no test suite, linter, or build step.

## Setup and running

```bash
source venv/bin/activate          # the venv is in ./venv (.gitignore also covers .venv)
pip install -r requirements.txt
python src/hello.py               # quick check that the API key works
python src/refund-checker/week1-Day5.py
```

`ANTHROPIC_API_KEY` lives in `.env` (gitignored). Only `src/hello.py` calls `load_dotenv()`. The `refund-checker` scripts create `anthropic.Anthropic()` directly, so the key has to already be in the environment (export it, or add `load_dotenv()`).

Every script calls the live API when it runs, so running one costs tokens.

## Structure and conventions

- `src/refund-checker/week1-DayN.py` holds one file per lesson day. The filenames contain hyphens, so they can't be imported as modules. Run them as scripts.
- Within a day file, earlier exercises are kept as commented-out blocks or bare `"""..."""` strings labelled `part 1`, `part 2`, `bonus`, and so on. Usually only the last block runs. Earlier outputs are pasted into `"""Output was- ..."""` strings as notes. Keep this style: comment out finished exercises instead of deleting them.
- Code is copied forward between days rather than shared, so `commitment_patterns`, `flag_refund_promise`, and the checker system prompt are duplicated in Day2, Day3, and Day5.
- Models used: `claude-haiku-5-5` (cheap checks) and `claude-sonnet-5-5`. `temperature` is deprecated on these models (see the Day2 notes). Use system prompts to control output instead.
- Response text is read with `response.content[-1].text` or by filtering for blocks where `block.type == "text"`.

## The refund-checker thread

The exercises across the week build up one idea: catch support-bot replies that promise a refund.
1. Day2: a system prompt forbids refund promises, and a regex detector (`flag_refund_promise`) scans the reply.
2. Day3: structured JSON output (`json.loads` on the model reply), plus an LLM-as-judge classifier (`{"promises_money_back": bool}`) compared against the regex.
3. Day4: multi-turn conversation by appending to a `history` list, watching `usage.input_tokens` grow.
4. Day5: a labelled `test_set` of `(sentence, truth)` pairs and a `score()` function that reports caught/false-alarm/missed counts and precision/recall for the regex and the model. Edge cases include conditional promises, paraphrases, negations, and instruction-override attempts.
