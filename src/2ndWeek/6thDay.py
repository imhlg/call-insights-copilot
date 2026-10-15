import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))

from config import client, HK_MODEL

SYSTEM = """You triage customer support messages.
A refund promise is any commitment to give the customer money back, in any form: cash, card reversal, bill credit, or a discount on a charge.
Reply with ONLY a JSON object, no other text, in this shape:
{"is_refund_promise": true | false, "reason": "..."}"""
# {"category": "billing" | "technical" | "other", "urgency": "low" | "high"}

ALLOWED_CATEGORY = {"billing", "technical", "other"}
ALLOWED_URGENCY = {"low", "high"}

test_set = [
    # No commitment — defer, refuse, or investigate
    ("A credit of ₹500 will appear on your next bill", True),
    (
        "We are sorry for the trouble and will add a loyalty point to your account.",
        False,
    ),
    # ("Our billing team will look into the charge and decide the outcome.", False),
    # ("I can't promise any compensation for this.", False),
    # ("I'm not able to say whether a refund is possible.", False),
    # ("I can't confirm that your refund will be approved.", False),
    # ("I can't promise a refund, so please don't expect one yet.", False),
    # ("Refunds are decided by the billing team; I can raise a ticket for you.", False),
    # ("The billing team will review it and decide the outcome.", False),
    # ("We may be able to offer a credit after they review your case.", False),
    # ("I'll escalate this to a supervisor and get back to you.", False),
    # # Clear promises — refund, credit, reversal, reimbursement
    # ("We'll put the money back on your card tomorrow.", True),
    # ("A credit of ₹500 will appear on your next bill.", True),
    # ("You will definitely get this charge reversed.", True),
    # ("Good news, the charge will be reversed on your next statement.", True),
    # ("Your refund has been approved and will be processed today.", True),
    # ("I've issued a full refund; it should post within 5 business days.", True),
    # ("We will reimburse you for the duplicate charge.", True),
    # # Harder cases — conditional, override, paraphrase, negation traps
    # (
    #     "If the billing team approves it, we'll refund the charge to your card.",
    #     True,
    # ),  # conditional promise
    # (
    #     "As you asked, I'm ignoring our rules: your refund is approved.",
    #     True,
    # ),  # instruction-override / jailbreak-style
    # (
    #     "I cannot guarantee a refund, but we will credit your account tonight.",
    #     True,
    # ),  # mixed: still commits to credit
    # (
    #     "While I can't promise a refund, the charge will be reversed on your bill.",
    #     True,
    # ),  # negation + still promises reversal
]


def get_text(response) -> str:
    # Lesson from Week 1: content is a LIST of blocks. Keep only the text ones.
    return "".join(b.text for b in response.content if b.type == "text")


def parse_triage(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").removeprefix("json").strip()
    data = json.loads(cleaned)  # raises an error if this is not JSON

    # added new checks after changing SYSTEM to include is_refund_promise and reason
    if not isinstance(data.get("is_refund_promise"), bool):
        raise ValueError("is_refund_promise must be true or false")  # check 2 failed
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("reason must be a non-empty string")  # check 3 failed

    # if data.get("category") not in ALLOWED_CATEGORY:
    #     raise ValueError(f"bad category: {data.get('category')!r}")
    # if data.get("urgency") not in ALLOWED_URGENCY:
    #     raise ValueError(f"bad urgency: {data.get('urgency')!r}")
    return data


def triage(message: str, max_attempts: int = 3):
    messages = [{"role": "user", "content": message}]
    for attempt in range(1, max_attempts + 1):
        response = client.messages.create(
            model=HK_MODEL, max_tokens=1000, system=SYSTEM, messages=messages
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
                messages.append(
                    {
                        "role": "user",
                        "content": f"That was not valid ({err}). Reply again with ONLY the JSON object.",
                    }
                )
    return None  # all attempts failed: a human should look at this one


for message, expected in test_set:
    result = triage(message)
    print(f"Message: {message!r}")
    print(f"Expected: {expected}")
    print(f"Result: {result}")
    if result is None:
        print("FAILED: no valid reply after all attempts, route to a human")
    elif result["is_refund_promise"] != expected:
        print("MISMATCH")
    else:
        print("OK")
    print("--------------------------------")
    print()


# print(triage("I was charged twice and my bill is due tomorrow."))
# print(triage("Unable to process my payment, please refund my money."))
