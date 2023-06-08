from functools import wraps

import httpx
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import ContextTypes

import bot.services.discourse as discourse_service
import bot.services.user as user_service
from bot.filters import HasUserInArgsFilter


def ensure_reply_or_mention(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.effective_message

        if msg.reply_to_message:
            from_user_id = msg.reply_to_message.from_user.id
            user = await user_service.get_by_id(from_user_id)
        elif HasUserInArgsFilter().filter(msg):
            username = context.args[0].replace("@", "").strip()
            user = await user_service.get_by_username(username)
        else:
            await msg.reply_text("❌ Вы должны ответить на сообщение пользователя или упомянуть его!")
            return

        return await func(update, context, user)

    return wrapper


def ensure_forum_account_is_linked(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        from_user = await user_service.get_by_id(update.effective_message.from_user.id)

        if not from_user.discourse_id:
            await update.effective_message.reply_text(
                "❌ Вы не привязали свой аккаунт к боту. " "Cделайте это с помощью команды /link."
            )
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


def ensure_user_is_forum_moderator(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        from_user = await user_service.get_by_id(update.effective_message.from_user.id)

        try:
            res = await discourse_service.get_user_by_id(from_user.discourse_id)

            if "moderator" not in res or not res["moderator"]:
                await update.effective_message.reply_text("❌ У вас недостаточно прав для выполнения этой команды.")
                return

        except httpx.HTTPError as e:
            await update.effective_message.reply_text("❌ Произошла ошибка при ваших данных пользователя.")
            return

        return await func(update, context, *args, **kwargs)

    return wrapper
