import uuid
import time

processed = {}
attempts_seen = 0


def crm_refund(amount, idem_key):
    global attempts_seen
    attempts_seen += 1
    if idem_key in processed:
        if processed[idem_key]["amount"] != amount:
            return 422, None
        else:
            return 200, processed[idem_key]

    result = {"status": "refunded", "amount": amount}
    processed[idem_key] = result          # the refund really happens

    if attempts_seen < 3:
        return 500, None                  # but the reply is lost
    return 200, result


def safe_refund(amount, max_attempts=4):
    key = str(uuid.uuid4())               # made ONCE, before the loop
    wait = 1
    for attempt in range(1, max_attempts + 1):
        status, body = crm_refund(amount, key)
        print(f"attempt {attempt}: status {status}")
        if status == 200:
            return body
        if status in (429, 500):
            time.sleep(wait)
            wait *= 2                     # 1s, 2s, 4s
            continue
        return None                       # 400: retry won't help
    return None


# key = str(uuid.uuid4())
# print(crm_refund(500, key))   # first call
# print(crm_refund(500, key))   # normal retry
# print(crm_refund(700, key))   # bad reuse
# print("refunds actually made:", len(processed))

# Acceptance criteria as code: a test that must pass before release
processed.clear()
key = str(uuid.uuid4())
crm_refund(500, key)                      # first call
crm_refund(500, key)                      # retry
assert len(processed) == 1, "retry must not create a second refund"
assert crm_refund(700, key)[0] == 422, "changed amount must be rejected"
print("acceptance criteria passed")

# Guardrail metric: duplicate refund rate from a refund log

refund_log = [
    {"customer": "C1", "order": "O9", "amount": 500, 'item': 23, "key": "k1"},
    {"customer": "C1", "order": "O9", "amount": 500, 'item': 23,
        "key": "k2"},  # retry with a new key
    {"customer": "C2", "order": "O4", "amount": 300, 'item': 24, "key": "k3"},
    {"customer": "C2", "order": "O4", "amount": 300, 'item': 29, "key": "k4"}
]

intents = [(r["customer"], r["order"], r["amount"], r['item'])
           for r in refund_log]
duplicates = len(intents) - len(set(intents))
print("duplicate refund rate:", duplicates / len(intents))
