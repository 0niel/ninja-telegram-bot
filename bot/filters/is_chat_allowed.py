import logging

from bot.config import get_settings

logger = logging.getLogger(__name__)
from telegram.ext.filters import MessageFilter


class IsChatAllowedFilter(MessageFilter):
    name = "is_chat_allowed"

    def filter(self, message):
        if len(get_settings().ALLOWED_CHATS) == 0:
            return True
        if message.chat_id in get_settings().ALLOWED_CHATS:
            return True
        logger.info(f"Somebody tried to use handler in not allowed chat '{message.chat.title}' ({message.chat_id})")
        return False
