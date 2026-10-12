from dotenv import load_dotenv
import anthropic

load_dotenv()                      # 1
client = anthropic.Anthropic()     # 2

response = client.messages.create(  # 3
    model="claude-haiku-5-5",
    max_tokens=100,
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)

for block in response.content:     # 4
    if block.type == "text":
        print(block.text)

print("stop_reason:", response.stop_reason)  # 5
