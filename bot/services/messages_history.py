import datetime

from bot.constants import SUPABASE_MESSAGES_HISTORY_TABLE
from bot.db import supabase
from bot.models import MessagesHistory


async def get_by_user_id(user_id: int, limit: int = 5, offset: int = 0):
    """Get user messages history"""

    response = (
        await supabase.table(SUPABASE_MESSAGES_HISTORY_TABLE)
        .select("*")
        .eq("tg_user_id", user_id)
        .order("date", desc=True)
        .range(offset, offset + limit)
        .execute()
    )
    return [MessagesHistory(**item) for item in response.data]


async def get_top_by_date(date: datetime.date, limit: int = 5):
    """Get top users by messages count"""
    response = (
        await supabase.table(SUPABASE_MESSAGES_HISTORY_TABLE)
        .select("*")
        .eq("date", date)
        .order("messages", desc=True)
        .limit(limit)
        .execute()
    )
    return [MessagesHistory(**item) for item in response.data]


async def add_message(user_id: int, date: datetime.date):
    """Add message to history. If message already exists, increment messages count"""
    date = date.strftime("%Y-%m-%d")

    response = (
        await supabase.table(SUPABASE_MESSAGES_HISTORY_TABLE)
        .select("*")
        .eq("tg_user_id", user_id)
        .eq("date", date)
        .execute()
    )
    if response.data:
        await supabase.table(SUPABASE_MESSAGES_HISTORY_TABLE).update({"messages": response.data[0]["messages"] + 1}).eq(
            "id", response.data[0]["id"]
        ).execute()
    else:
        await supabase.table(SUPABASE_MESSAGES_HISTORY_TABLE).insert(
            {"tg_user_id": user_id, "date": date, "messages": 1}
        ).execute()
