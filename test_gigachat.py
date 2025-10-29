import uuid, requests

url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
auth_key = "Nzc0MjE1MGUtMjU1MS00NTA0LTk0YjYtNmU4NzY5Njc5NTZhOmFjNTM5MTE1LTFlNWEtNGNiYS1hYjBlLTk4YzA5YWE5ZjY3OA=="
scopes = ["GIGACHAT_API_PERS","GIGACHAT_API_B2B","GIGACHAT_API_CORP"]

for s in scopes:
    r = requests.post(
        url,
        headers={
            "Content-Type":"application/x-www-form-urlencoded",
            "Accept":"application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {auth_key}",
        },
        data={"grant_type":"client_credentials","scope":s},
        verify="russian_trusted_root_ca_pem.crt",
        timeout=30,
    )
    print(s, r.status_code, r.text)
