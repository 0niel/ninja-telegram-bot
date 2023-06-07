from bot.constants import SUPABASE_REPUTATION_UPDATES_TABLE
from bot.db import supabase
from bot.models import ReputationUpdate


async def create(reputation_update: ReputationUpdate) -> None:
    """Create reputation update"""

    await supabase.table(SUPABASE_REPUTATION_UPDATES_TABLE).insert(reputation_update.dict(exclude={"id"})).execute()


async def get_by_user_id(user_id: int, limit=100) -> list[ReputationUpdate]:
    """Get user reputation history"""
    response = (
        await supabase.table(SUPABASE_REPUTATION_UPDATES_TABLE)
        .select("*")
        .eq("to_tg_user_id", user_id)
        .order("updated_at", desc=True)
        .limit(limit)
        .execute()
    )
    return [ReputationUpdate(**item) for item in response.data]


async def is_user_send_rep_to_message(user_id: int, message_id: int) -> bool:
    """Check if user send reputation to message"""

    response = (
        await supabase.table(SUPABASE_REPUTATION_UPDATES_TABLE)
        .select("*")
        .eq("from_tg_user_id", user_id)
        .eq("message_id", message_id)
        .execute()
    )
    return bool(response.data)
