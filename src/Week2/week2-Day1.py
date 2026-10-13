import json
from config import client

MODEL = "claude-haiku-5-5"

SYSTEM = """You triage customer support messages.
Reply with ONLY a JSON object, no other text, in this shape:
{"category": "billing" | "technical" | "other", "urgency": "low" | "high"}"""

ALLOWED_CATEGORY = {"billing", "technical", "other"}
ALLOWED_URGENCY = {"low", "high"}


def get_text(response) -> str:
    # Lesson from Week 1: content is a LIST of blocks. Keep only the text ones.
    return "".join(b.text for b in response.content if b.type == "text")


def parse_triage(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").removeprefix("json").strip()
    data = json.loads(cleaned)  # raises an error if this is not JSON
    if data.get("category") not in ALLOWED_CATEGORY:
        raise ValueError(f"bad category: {data.get('category')!r}")
    if data.get("urgency") not in ALLOWED_URGENCY:
        raise ValueError(f"bad urgency: {data.get('urgency')!r}")
    return data


def triage(message: str, max_attempts: int = 3):
    messages = [{"role": "user", "content": message}]
    for attempt in range(1, max_attempts + 1):
        response = client.messages.create(
            model=MODEL, max_tokens=1000, system=SYSTEM, messages=messages
        )
        if response.stop_reason == "max_tokens":
            print(f"attempt {attempt}: reply cut off, retrying")
            continue
        raw = get_text(response)
        try:
            return parse_triage(raw)
        except ValueError as err:
            print(f"attempt {attempt}: {err}")
            if raw:
                messages.append({"role": "assistant", "content": raw})
                messages.append({
                    "role": "user",
                    "content": f"That was not valid ({err}). Reply again with ONLY the JSON object.",
                })
    return None  # all attempts failed: a human should look at this one


print(triage("I was charged twice and my bill is due tomorrow."))
print(triage("The app crashes whenever I open settings, no rush."))
