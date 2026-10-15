import requests

response = requests.get("https://jsonplaceholder.typicode.com/todos/1")
response2 = requests.get("https://jsonplaceholder.typicode.com/todos/99999")

# data = response.json()

# print("title", data["title"])
# print("completed", data["completed"])
# print(type(data))

# try:
#     response2.raise_for_status()
# except requests.HTTPError as e:
#     print("Error: ", e.response.status_code)
#     print("Error: ", e.response.text)


# def get_todo(todo_id):
#     url = f"https://jsonplaceholder.typicode.com/todos/{todo_id}"
#     try:
#         response = requests.get(url, timeout=5)
#         response.raise_for_status()
#         return response.json()
#     except requests.RequestException as err:
#         print("failed:", err)
#         return None


# print(get_todo(1))
# print(get_todo(99999))


try:
    requests.get("https://doesnotexisturlhhgflf.sample.com")
except requests.RequestException as err:
    # print("failed:", err)
    print("error type:", type(err))
    print(type(err).__name__)
