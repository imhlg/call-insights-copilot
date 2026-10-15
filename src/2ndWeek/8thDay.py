import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))

from config import client, HK_MODEL


def generate_response(user_message):
    response = client.messages.create(
        model=HK_MODEL,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[-1].text


FAQS = {
    "refunds": "Refunds go back to your original card within 5 to 7 business days after approval. To ask for one, open a ticket with your invoice number.",
    "billing_dispute": "If you see a charge you do not recognise, raise a billing dispute within 30 days. Our billing team replies within 3 working days.",
    "bill_credit": "A bill credit lowers your next monthly bill. We give bill credits when a service outage lasts longer than 4 hours.",
    "plan_change": "You can change your mobile plan any time in the app. Upgrades start right away, and downgrades start from your next billing cycle.",
    "password_reset": "To reset your password, tap Forgot Password on the login screen. The reset link is sent to your email and expires in 15 minutes.",
}


hlcleaned = FAQS["refunds"].split(" ")
for i, word in enumerate(hlcleaned):
    word = word.lower()
    for punc in [
        ".",
        ",",
        "!",
        "?",
        ":",
        ";",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        "|",
        "\\",
        "/",
        "*",
    ]:
        word = word.replace(punc, "")
    hlcleaned[i] = word

print(hlcleaned)


question = "How do I get a Refund?"
words = question.lower().replace("?", "").split()
print(words)
