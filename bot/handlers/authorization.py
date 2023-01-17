import json
import logging
from datetime import datetime

import httpx
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, Response
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType
from telegram.ext import CallbackContext, CommandHandler

from bot import application
from bot.config import get_settings
from bot.filters import HasUserInArgsFilter
from bot.services import user as user_service
from bot.services.auto_delete import auto_delete
from bot.utils.user_api_keys import decode_payload, generate_auth_url, generate_nonce

logger = logging.getLogger(__name__)


async def auth_redirect_callback(request: Request) -> Response:
    """
    Callback for discourse auth. Redirected from Mirea Ninja with a param a ?payload=[the API KEY].
    """
    payload = request.query_params.get("payload")

    private_key: str = application.bot_data["private_key"]

    bot_deeplink_url = f"https://t.me/{application.bot.username}?start="

    if not payload:
        return RedirectResponse(url=f"{bot_deeplink_url}Ошибка авторизации")

    payload = json.loads(decode_payload(payload, private_key))
    key, nonce = payload["key"], payload["nonce"]

    user = await user_service.get_by_discourse_nonce(nonce)

    if not user:
        return RedirectResponse(url=f"{bot_deeplink_url}Ошибка авторизации")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{get_settings().DISCOURSE_URL}/session/current.json",
            headers={"User-Api-Key": key},
        )

        if response.status_code != 200:
            return RedirectResponse(url=f"{bot_deeplink_url}Ошибка авторизации")

        session = response.json()

    discourse_id = session["current_user"]["id"]

    await user_service.update_discourse_data(user.id, discourse_id, key)

    return RedirectResponse(url=f"{bot_deeplink_url}Аккаунт привязан")


async def auth_deeplink_callback(update: Update, context: CallbackContext) -> None:
    if not update.effective_message:
        return

    if update.effective_chat.type != ChatType.PRIVATE:
        msg = await update.effective_message.reply_text("❌ Аутентификация доступна только в личных сообщениях бота.")
        auto_delete(msg, context, from_message=update.effective_message)
        return

    user = await user_service.get_by_id(update.effective_user.id)

    if not user:
        return

    if "auth" in update.effective_message.text:
        await auth(update, context)
        return

    if "Ошибка" in update.effective_message.text:
        await update.effective_message.reply_text("❌ Произошла ошибка при авторизации. Попробуйте еще раз.")
        return

    logger.info("User %s has successfully authenticated", user.id)
    await update.effective_message.reply_text("✅ Аккаунт Mirea Ninja успешно привязан к боту.")


async def auth(update: Update, context: CallbackContext) -> None:
    if not get_settings().RUN_WITH_WEBHOOK:
        await update.effective_message.reply_text(
            "❌ Бот не поддерживает в данный момент авторизацию через команду /auth. \n\n"
            "Обратитесь к администратору для подробностей.",
        )
        return

    if update.effective_chat.type != ChatType.PRIVATE:
        button = InlineKeyboardButton("🔗 Перейти", url=f"https://t.me/{application.bot.username}?start=auth")
        keyboard = InlineKeyboardMarkup([[button]])
        msg = await update.effective_message.reply_text(
            "❌ Аутентификация доступна только в личных сообщениях бота.", reply_markup=keyboard
        )
        auto_delete(msg, context, from_message=update.effective_message)
        return

    user = await user_service.get_by_id(update.effective_user.id)

    if not user:
        return

    if user.discourse_id:
        await update.effective_message.reply_text("✅ Вы уже привязали свой аккаунт к боту.")
        return

    nonce = generate_nonce()
    await user_service.set_discourse_nonce(update.effective_user.id, nonce)
    auth_url = generate_auth_url(update.effective_user.id, context.bot_data["public_key"], nonce)

    button = InlineKeyboardButton(
        "🔑 Аутентификация",
        url=auth_url,
    )
    keyboard = InlineKeyboardMarkup.from_button(button)

    await update.effective_message.reply_text(
        "Для привязки аккаунта Mirea Ninja к боту нажмите на кнопку ниже.",
        reply_markup=keyboard,
    )


async def whois(update: Update, context: CallbackContext) -> None:
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

    if not user:
        new_message = await msg.reply_text("❌ Пользователь не найден!")
        auto_delete(new_message, context, from_message=msg)
        return

    if not user.discourse_id:
        new_message = await msg.reply_text("❌ Пользователь не привязал свой аккаунт к боту.")
        auto_delete(new_message, context, from_message=msg)
        return

    async with httpx.AsyncClient() as client:
        headers = {
            "Api-Key": get_settings().DISCOURSE_API_KEY,
            "Api-Username": "system",
        }

        response = await client.get(f"{get_settings().DISCOURSE_URL}/admin/users/{user.discourse_id}.json", headers=headers)

        if response.status_code != 200:
            logger.error("Failed to get user info from Mirea Ninja: %s", response.text)
            new_message = await msg.reply_text("❌ Произошла ошибка при получении данных пользователя.")
            auto_delete(new_message, context, from_message=msg)
            return

        data = response.json()

        if not data["id"]:
            new_message = await msg.reply_text("❌ Пользователь не найден.")
            auto_delete(new_message, context, from_message=msg)
            return

        admin_text = "👑 Администратор" if data["admin"] else ""
        moderator_text = "🔨 Модератор" if data["moderator"] else ""
        created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        created_at_text = created_at.strftime("%d.%m.%Y %H:%M:%S")

        text = (
            f"👤 Информация о пользователе {user['username']}:\n\n"
            f"📅 Дата регистрации: {created_at_text}\n"
            f"📊 Количество сообщений: {data['post_count']}\n"
            f"📈 Количество лайков: {data['like_count']}\n"
            f"📊 Уровень доверия: {data['trust_level']}\n"
            f"{admin_text} {moderator_text}"
        )

        await msg.reply_text(text)


application.add_handler(CommandHandler("start", auth_deeplink_callback), group=1)
application.add_handler(CommandHandler(["auth", "connect", "link"], auth), group=1)
application.add_handler(CommandHandler("whois", whois), group=1)
