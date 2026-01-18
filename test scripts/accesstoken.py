import requests

access_token = "ya29.a0AQQ_BDSWzE9IYUNS4JtlS_JgQ58uhrGsEL_Uo7IDXQwyLJBRK9-RF1AZ27uj4fFwA7MCdR2TbeMUikdEb0RyGJsm7UAh50rUVKlT853AvDCThP80iL3IcneyNL_3_tdGdBABsFkCJYOU8cGSHnSo7-FWCu7G9lFGDDwshk4Cv3EttOjodrk9mm_4phA-ff5Ij8GkEIIaCgYKARcSARYSFQHGX2MiJcuh1dX6SHhuPZYIA9BStA0206"

response = requests.get(
    "https://www.googleapis.com/oauth2/v2/userinfo",
    headers={"Authorization": f"Bearer {access_token}"}
)

print(response.json())