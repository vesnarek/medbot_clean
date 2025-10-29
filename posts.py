import base64
client_id = "7742150e-2551-4504-94b6-6e876967956a"
client_secret = "Nzc0MjE1MGUtMjU1MS00NTA0LTk0YjYtNmU4NzY5Njc5NTZhOjRiODQ4ZWQ1LWJlN2QtNDRmYS04MGVjLTNhMWJjMzM3OWNjZg=="
basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
print("Authorization:", "Basic " + basic)
