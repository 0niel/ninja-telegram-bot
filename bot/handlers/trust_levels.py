import logging
import re

import httpx
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from bot import application
from bot.filters import HasUserInArgsFilter
from bot.services import user as user_service
from bot.services.auto_delete import auto_delete
from bot.services.discourse import get_user_by_id, set_user_trust_level

logger = logging.getLogger(__name__)


async def tl(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message

    if msg.reply_to_message:
        from_user_id = msg.reply_to_message.from_user.id
        user = await user_service.get_by_id(from_user_id)
    elif HasUserInArgsFilter().filter(msg):
        username = context.args[0].replace("@", "").strip()
        user = await user_service.get_by_username(username)
    else:
        new_message = await msg.reply_text("❌ Вы должны ответить на сообщение пользователя или упомянуть его!")
        auto_delete(new_message, context, from_message=msg)
        return

    from_user = await user_service.get_by_id(msg.from_user.id)

    if not from_user.discourse_id:
        new_message = await msg.reply_text("❌ Вы не привязали свой аккаунт к боту.")
        auto_delete(new_message, context, from_message=msg)
        return

    try:
        res = await get_user_by_id(from_user.discourse_id)

        if "moderator" not in res or not res["moderator"]:
            new_message = await msg.reply_text("❌ У вас недостаточно прав для выполнения этой команды.")
            auto_delete(new_message, context, from_message=msg)
            return

    except httpx.HTTPError as e:
        new_message = await msg.reply_text("❌ Произошла ошибка при ваших данных пользователя.")
        auto_delete(new_message, context, from_message=msg)
        return

    trust_level = -1
    if re.search(r"\d+$", context.args[-1]):
        trust_level = int(context.args[-1])

    if trust_level < 0 or trust_level > 4:
        new_message = await msg.reply_text("❌ Вы должны указать уровень доверия, например: /tl @username 2")
        auto_delete(new_message, context, from_message=msg)
        return

    if not user:
        new_message = await msg.reply_text("❌ Пользователь не найден!")
        auto_delete(new_message, context, from_message=msg)
        return

    if not user.discourse_id:
        new_message = await msg.reply_text("❌ Пользователь не привязал свой аккаунт к боту.")
        auto_delete(new_message, context, from_message=msg)
        return

    try:
        await set_user_trust_level(user.discourse_id, trust_level)
        new_features_text = " Теперь ему доступны новые возможности" if trust_level > 2 else ""
        new_message = await msg.reply_text(
            f"✅ Уровень доверия пользователя {user.username} был изменен на {trust_level}.{new_features_text}"
        )
        auto_delete(new_message, context, from_message=msg)

    except httpx.HTTPError as e:
        new_message = await msg.reply_text("❌ Произошла ошибка при получении данных пользователя.")
        auto_delete(new_message, context, from_message=msg)
        return


application.add_handler(CommandHandler("tl", tl), group=1)
