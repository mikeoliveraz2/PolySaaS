import requests

access_token = "ya29.a0AQQ_BDTZvemVvqN-qoAwDlWCgeVebtaKsMmmJqr1ljFBnFxZoSPj0TGHuYhgnThfdM2Y8ZQHG3PqtjGtAPYjFUAUzThY39lMxydvpOStVB7kdQfPgRbCsdhNWj2UfaFLYdkWhSa1Gb2g_tvxFn1M14fblxUBt2os_VVhvWIHS0PAKEozbe8ufnt9lBsM2wnaFq865XAaCgYKATsSARESFQHGX2MiAl7jYm3PVKb2qiPlzbBqOQ0206"

response = requests.get(
    "https://www.googleapis.com/oauth2/v2/userinfo",
    headers={"Authorization": f"Bearer {access_token}"}
)

print(response.json())