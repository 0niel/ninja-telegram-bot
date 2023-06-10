import logging
import re

import httpx
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

from bot import application
from bot.models import User
from bot.services.discourse import set_user_trust_level
from bot.utils.decorators import ensure_forum_account_is_linked
from bot.utils.decorators import ensure_reply_or_mention
from bot.utils.decorators import ensure_user_is_forum_moderator

logger = logging.getLogger(__name__)


@ensure_reply_or_mention
@ensure_forum_account_is_linked
@ensure_user_is_forum_moderator
async def tl(update: Update, context: CallbackContext, target_user: User | None = None) -> None:
    msg = update.effective_message

    trust_level = -1
    if re.search(r"\d+$", context.args[-1]):
        trust_level = int(context.args[-1])

    if trust_level < 0 or trust_level > 4:
        await msg.reply_text("❌ Вы должны указать уровень доверия, например: /tl @username 2")
        return

    if not target_user:
        await msg.reply_text("❌ Пользователь не найден!")
        return

    if not target_user.discourse_id:
        await msg.reply_text("❌ Пользователь не привязал свой аккаунт к боту.")
        return

    try:
        await set_user_trust_level(target_user.discourse_id, trust_level)
        new_features_text = " Теперь ему доступны новые возможности" if trust_level > 2 else ""
        await msg.reply_text(
            f"✅ Уровень доверия пользователя {target_user.username} был изменен на {trust_level}.{new_features_text}"
        )

    except httpx.HTTPError as e:
        await msg.reply_text("❌ Произошла ошибка при получении данных пользователя.")
        return


application.add_handler(CommandHandler("tl", tl))
