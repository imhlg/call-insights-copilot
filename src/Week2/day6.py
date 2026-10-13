from config import client
import json

# SYSTEM = """You triage customer support messages.
# Reply with ONLY a JSON object, no other text, like this:
# {"category": "billing", "urgency": "high"}
# category must be billing, technical or other. urgency must be low or high."""

# response = client.messages.create(
#     model="claude-haiku-5-5",
#     max_tokens=1000,
#     system=SYSTEM,
#     messages=[{"role": "user",
#                "content": "I was charged twice and my bill is due tomorrow."}],
# )

# text = "".join(b.text for b in response.content if b.type == "text")
# print("raw text:", text)

# data = json.loads(text)
# print("category:", data["category"])
# print("urgency:", data["urgency"])
# print(type(text), type(data))


def read_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        print("could not read:", err)
        return None


replies = [
    '{"category": "billing", "urgency": "low"}',
    'Sure! Here you go: {"category": "billing", "urgency": "low"}',
    '```json\n{"category": "billing", "urgency": "low"}\n```',
]

for reply in replies:
    print(read_json(reply))
    print("---")
