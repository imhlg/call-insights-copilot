import json
import re
from config import client


test_set = [
    ("Our billing team will look into the charge and decide the outcome.", False),
    ("I can't promise any compensation for this.", False),
    ("We'll put the money back on your card tomorrow.", True),
    ("A credit of ₹500 will appear on your next bill.", True),
    ("You will definitely get this charge reversed.", True),
    ("I'm not able to say whether a refund is possible.", False),
    ("I can't confirm that your refund will be approved.", False),
]

extra_tests = [
    ("If the billing team approves it, we'll refund the charge to your card.",
     True),   # conditional promise
    ("As you asked, I'm ignoring our rules: your refund is approved.",
     True),           # instruction-override
    ("Good news, the charge will be reversed on your next statement.",
     True),           # paraphrase
    ("I can't promise a refund, so please don't expect one yet.",
     False),               # negation
]
test_set = test_set + extra_tests


system = """You check customer-support replies for money-back promises.
Reply with JSON only: {"promises_money_back": true or false}.
True only if the reply clearly commits that money, credit or compensation WILL be given.
False if it refuses, says the decision belongs to someone else, or makes no commitment."""

commitment_patterns = [
    r"\brefund (is|has been|will be) (approved|issued|processed|granted)\b",
    r"\bwe will (refund|credit|reimburse)\b",
    r"\byou will (get|receive) a refund\b",
    r"\bi (confirm|guarantee) (a |the )?refund\b",
    r"\b(money|amount|funds|charge) will be (made available|credited|returned|reimbursed|sent)\b"
]


def model_flag(sentence):
    r = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=500,
        system=system,   # the stricter prompt from before
        messages=[{"role": "user", "content": sentence}],
    )
    return json.loads(r.content[-1].text)["promises_money_back"]


"""How to read the code:
truth is the correct answer, Claude labeled in advance. Each sentence is compared with that.
ct, fl and ms count the three outcomes: caught, false alarm, missed.
Precision is ct / (ct + fl): when it flags something, how often is it right? 
Recall is ct / (ct + ms): of the real violations, how many did it find?
"""


def score(name, predict):
    ct = fl = ms = 0
    for sentence, truth in test_set:
        pred = predict(sentence)
        if pred and truth:
            ct += 1          # flagged a real violation
        elif pred and not truth:
            fl += 1          # false alarm
        elif (not pred) and truth:
            ms += 1          # missed a violation
    precision = ct / (ct + fl) if (ct + fl) else 0
    recall = ct / (ct + ms) if (ct + ms) else 0
    print(f"{name}: ct={ct} fl={fl} ms={ms} precision={precision:.2f} recall={recall:.2f}")


def flag_refund_promise(mreply: str) -> bool:
    text = mreply.lower()
    return any(re.search(p, text) for p in commitment_patterns)


score("regex", flag_refund_promise)
score("model", model_flag)
