import re

# Shared by the week 1 refund-checker exercises (Day 2, 3, 5).
REFUND_CHECK_SYSTEM = """You check customer-support replies for money-back promises.
Reply with JSON only: {"promises_money_back": true or false}.
True only if the reply clearly commits that money, credit or compensation WILL be given.
False if it refuses, says the decision belongs to someone else, or makes no commitment."""

commitment_patterns = [
    r"\brefund (is|has been|will be) (approved|issued|processed|granted)\b",
    r"\bwe will (refund|credit|reimburse)\b",
    r"\byou will (get|receive) a refund\b",
    r"\bi (confirm|guarantee) (a |the )?refund\b",
    r"\b(money|amount|funds|charge) will be (made available|credited|returned|reimbursed|sent)\b",
]


def flag_refund_promise(mreply: str) -> bool:
    text = mreply.lower()
    return any(re.search(p, text) for p in commitment_patterns)
