from config import client
"""part-1"""
response = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=150,
    messages=[{"role": "user",
               "content": "Say hello and give one fact about contact centers."}]
)

print(response.content[0].text)
print("\nInput tokens:", response.usage.input_tokens)
print("Output tokens:", response.usage.output_tokens)

"""part-2"""
# response = client.messages.create(
#     model="claude-sonnet-5-5",
#     max_tokens=200,
#     messages=[
#         {"role": "user", "content": "Complete this sentence: The head of MIT is"}]
# )
# # print(response.content[0].text)
# for block in response.content:
#     if block.type == "text":
#         print(block.text)

# print("lenght is ", len(response.content))
# print("Block types:", [b.type for b in response.content])
# print("Stop reason:", response.stop_reason)
