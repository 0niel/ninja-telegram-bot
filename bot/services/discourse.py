import httpx

from bot.config import get_settings

headers = {
    "Api-Key": get_settings().DISCOURSE_API_KEY,
    "Api-Username": "system",
}


async def set_user_trust_level(discourse_id: int, new_trust_level: int):
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{get_settings().DISCOURSE_URL}/admin/users/{discourse_id}/trust_level",
            headers=headers,
            json={"level": new_trust_level},
        )

        response.raise_for_status()


async def get_user_by_id(discourse_id: int) -> dict:
    async with httpx.AsyncClient() as client:

        response = await client.get(f"{get_settings().DISCOURSE_URL}/admin/users/{discourse_id}.json", headers=headers)

        response.raise_for_status()

        return response.json()
