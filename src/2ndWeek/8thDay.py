import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))

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

# print(hlcleaned)

# question = "How do I get a Refund?"
# question = "Can I get a charge reversed?"
question = "I want my money back"
words = question.lower().replace("?", "").split()
# print(words)

# for word in words:
#     if word in hlcleaned:
#         print("found", word)
# else:
#     print("No match found")


# def score(question_words, faq_text):
#     faq_words = faq_text.lower().replace(".", "").replace(",", "").split()
#     return sum(1 for w in question_words if w in faq_words)


# question_words = ["how", "do", "i", "get", "a", "refund"]
# for name, text in FAQS.items():
#     print(name, score(question_words, text))

STOP_WORDS = {
    "how",
    "do",
    "i",
    "get",
    "a",
    "can",
    "the",
    "to",
    "with",
    "we",
    "for",
    "from",
    "no",
}
SYNONYMS = {
    "refund": ["money", "reversal", "reversed", "return"],
    "money": ["refund", "reversal", "reversed", "return"],
    "back": ["refund", "return"],
}

# question_words = ["can", "i", "get", "a", "charge", "reversed"]
question_words = ["i", "want", "my", "money", "back"]
key_words = [w for w in question_words if w not in STOP_WORDS]
# print(key_words)

expanded = list(key_words)
for word in key_words:
    expanded += SYNONYMS.get(word, [])
print(expanded)

expanded = set(key_words)
for word in key_words:
    expanded.update(SYNONYMS.get(word, []))
print(expanded)


def score2(key_words, faq_text):
    faq_text = faq_text.lower()
    return sum(1 for w in key_words if w in faq_text)


for name, text in FAQS.items():
    print(name, score2(expanded, text))


def best_faq(scores, threshold=0.5):
    best = max(scores, key=scores.get)
    # best = max(scores, key=lambda name: scores[name])
    if scores[best] < threshold:
        return None
    return best


def answer(scores, faqs, threshold=0.5):
    name = best_faq(scores, threshold)
    if name is None:
        return {"answer": None, "source": None, "note": "no good match, send to a human"}
    return {"answer": faqs[name], "source": name, "score": scores.get(name)}


# print(answer({"refunds": 0.998, "bill_credit": 0.974, "plan_change": 0.281}, FAQS))
print(answer({"refunds": 0.31, "bill_credit": 0.22, "plan_change": 0.18}, FAQS))
