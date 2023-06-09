from datetime import datetime
from typing import List

from postgrest import APIResponse

from bot import timezone_offset
from bot.constants import SUPABASE_USERS_TABLE
from bot.db import supabase
from bot.models import User


async def update_user_names(user_id: int, username: str, first_name: str, last_name: str):
    response: APIResponse = await supabase.table(SUPABASE_USERS_TABLE).select("*").eq("id", user_id).execute()

    if response.data:
        user = User(**response.data[0])
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        await supabase.table(SUPABASE_USERS_TABLE).update(
            {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            }
        ).eq("id", user_id).execute()
    else:
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        await supabase.table(SUPABASE_USERS_TABLE).insert(user.dict(exclude={"id", "updated_at", "created_at", "update_reputation_at"})).execute()


async def get_by_id(user_id: int) -> User | None:
    response: APIResponse = await supabase.table(SUPABASE_USERS_TABLE).select("*").eq("id", user_id).execute()

    return User(**response.data[0]) if response.data else None


async def set_discourse_nonce(user_id: int, nonce: str):

    await supabase.table(SUPABASE_USERS_TABLE).update({"discourse_request_nonce": nonce}).eq("id", user_id).execute()


async def get_by_discourse_nonce(nonce: str) -> User | None:
    response: APIResponse = (
        await supabase.table(SUPABASE_USERS_TABLE).select("*").eq("discourse_request_nonce", nonce).single().execute()
    )

    if response.data:
        return User(**response.data)


async def update_discourse_data(user_id: int, discourse_id: int, discourse_api_key: str):
    await supabase.table(SUPABASE_USERS_TABLE).update(
        {"discourse_id": discourse_id, "discourse_api_key": discourse_api_key}
    ).eq("id", user_id).execute()


async def set_discourse_notifications_enabled(user_id: int, enabled: bool):
    await supabase.table(SUPABASE_USERS_TABLE).update({"discourse_notifications_enabled": enabled}).eq(
        "id", user_id
    ).execute()


async def get_by_discourse_id(discourse_id: int) -> User | None:
    response: APIResponse = (
        await supabase.table(SUPABASE_USERS_TABLE).select("*").eq("discourse_id", discourse_id).execute()
    )

    return User(**response.data[0]) if response.data else None


async def get_by_username(username: str) -> User | None:
    response: APIResponse = (
        await supabase.table(SUPABASE_USERS_TABLE).select("*").eq("username", username).single().execute()
    )

    if response.data:
        return User(**response.data)


async def update_rep_and_force(from_user_id: int, to_user_id: int, new_rep: float, new_force: float):
    await supabase.table(SUPABASE_USERS_TABLE).update({"reputation": new_rep, "force": new_force}).eq(
        "id", to_user_id
    ).execute()
    serializable_datetime = datetime.now(timezone_offset).isoformat()
    await supabase.table(SUPABASE_USERS_TABLE).update({"update_reputation_at": serializable_datetime}).eq(
        "id", from_user_id
    ).execute()


async def update_force(user_id: int, new_force: float):
    """Update force of user"""
    await supabase.table(SUPABASE_USERS_TABLE).update({"force": new_force}).eq("id", user_id).execute()


def is_rep_change_available(user: User, cooldown_seconds: int) -> bool:
    """Check if user can change reputation"""
    second = (datetime.now(timezone_offset) - user.update_reputation_at.replace(tzinfo=timezone_offset)).total_seconds()

    return second >= cooldown_seconds


async def get_top_by_reputation(limit: int):
    """Get top users by reputation"""
    response: APIResponse = (
        await supabase.table(SUPABASE_USERS_TABLE).select("*").order("reputation", desc=True).limit(limit).execute()
    )
    return [User(**user) for user in response.data]


async def get_rating_slice(user_id, before_count: int, after_count: int) -> List[tuple[User, int]]:
    """Get slice of users rating. It's used to show user rating in rating command.  For example, if user has 1000
    rating, and before_count=5 and after_count=5, this function will return 10 users (5 before and 5 after user).
    This function also returns user position in rating"""

    response: APIResponse = (
        await supabase.table(SUPABASE_USERS_TABLE).select("*").order("reputation", desc=True).limit(1000).execute()
    )

    users = [User(**user) for user in response.data]

    user_position = next((i for i, user in enumerate(users) if user.id == user_id), 0)
    return [
        (user, user_position + i + 1)
        for i, user in enumerate(users[max(0, user_position - before_count) : user_position + after_count + 1])
    ]
