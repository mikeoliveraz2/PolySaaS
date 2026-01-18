import requests

access_token = "ya29.a0AQQ_BDRo4e5OSwO4J9e5x5nKa8wR20HMaL3DmWiAfdgw6Ipx7We1fcOpsoLK-gykYVYG-A90XUyxzlxjsAKWF7FqJXB2MbQ4znoXgDTOTUsDHYXoj6JvVLJ-3PAoW7DkJ2OayaE-Qj38mR1qUQ-nqASqyfMnfhb_BLrhMjO8tfWzKtiJqFOSUR1Pj7yD5xAJROzFQwQaCgYKAW4SARYSFQHGX2Mit-ba0eA5z5onxXS6-5uRXg0206"

response = requests.get(
    "https://www.googleapis.com/oauth2/v2/userinfo",
    headers={"Authorization": f"Bearer {access_token}"}
)

print(response.json())