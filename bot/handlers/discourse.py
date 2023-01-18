import json
import logging
from datetime import datetime
from enum import IntEnum

import httpx
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, Response
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ChatType, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters

from bot import application
from bot.config import get_settings
from bot.filters import HasUserInArgsFilter
from bot.services import user as user_service
from bot.services.auto_delete import auto_delete
from bot.utils.user_api_keys import decode_payload, generate_auth_url, generate_nonce

logger = logging.getLogger(__name__)


class NotificationType(IntEnum):
    MENTIONED = 1
    REPLIED = 2
    QUOTED = 3
    EDITED = 4
    LIKED = 5
    PRIVATE_MESSAGE = 6
    INVITED_TO_PRIVATE_MESSAGE = 7
    INVITEE_ACCEPTED = 8
    POSTED = 9
    MOVED_POST = 10
    LINKED = 11
    GRANTED_BADGE = 12
    INVITED_TO_TOPIC = 13
    CUSTOM = 14
    GROUP_MENTIONED = 15
    GROUP_MESSAGE_SUMMARY = 16
    WATCHING_FIRST_POST = 17
    TOPIC_REMINDER = 18
    LIKED_CONSOLIDATED = 19
    POST_APPROVED = 20
    CODE_REVIEW_COMMIT_APPROVED = 21
    MEMBERSHIP_REQUEST_ACCEPTED = 22
    MEMBERSHIP_REQUEST_CONSOLIDATED = 23
    BOOKMARK_REMINDER = 24
    REACTION = 25
    VOTES_RELEASED = 26
    EVENT_REMINDER = 27
    EVENT_INVITATION = 28
    CHAT_MENTION = 29
    CHAT_MESSAGE = 30
    ASSIGNED = 34


async def push(request: Request) -> Response:
    """
    Callback for discourse push notifications.
    """

    payload = await request.body()
    payload = json.loads(payload)

    notifications = payload["notifications"]

    bot = application.bot

    messages = []
    for notification in notifications:
        client_id = int(notification["client_id"])
        user = await user_service.get_by_id(client_id)

        if user is None:
            continue

        if user.discourse_id is None:
            continue

        if not user.discourse_notifications_enabled:
            continue

        notification_type = NotificationType(notification["notification_type"])

        if notification_type == NotificationType.TOPIC_REMINDER:
            emoji_message = "📌"
        elif notification_type == NotificationType.LIKED_CONSOLIDATED:
            emoji_message = "👍"
        elif notification_type == NotificationType.POST_APPROVED:
            emoji_message = "✅"
        elif notification_type == NotificationType.MEMBERSHIP_REQUEST_ACCEPTED:
            emoji_message = "🎉"
        elif notification_type == NotificationType.MEMBERSHIP_REQUEST_CONSOLIDATED:
            emoji_message = "🎉"
        elif notification_type == NotificationType.BOOKMARK_REMINDER:
            emoji_message = "📌"
        elif notification_type == NotificationType.REACTION:
            emoji_message = "👍"
        elif notification_type == NotificationType.VOTES_RELEASED:
            emoji_message = "🗳"
        elif notification_type == NotificationType.EVENT_REMINDER:
            emoji_message = "📅"
        elif notification_type == NotificationType.EVENT_INVITATION:
            emoji_message = "📅"
        elif notification_type == NotificationType.ASSIGNED:
            emoji_message = "📌"
        elif notification_type == NotificationType.PRIVATE_MESSAGE:
            emoji_message = "📨"
        elif notification_type == NotificationType.INVITED_TO_PRIVATE_MESSAGE:
            emoji_message = "📨"
        elif notification_type == NotificationType.POSTED:
            emoji_message = "💬"
        else:
            emoji_message = "❓"

        message = (
            f"{emoji_message} <a href='{notification['url']}'>{notification['topic_title']}</a>\n\n"
            f"{notification['excerpt']}"
        )
        messages.append((user.id, message))

    for user_id, message in messages:
        await bot.send_message(user_id, message, parse_mode=ParseMode.HTML)

    return Response(status_code=200)


class AuthResult(IntEnum):
    SUCCESS = 0
    ACCOUNT_ALREADY_LINKED = 1
    ERROR = 2


ENABLE_NOTIFICATIONS_MESSAGE = "🔔 Включить уведомления"
DISABLE_NOTIFICATIONS_MESSAGE = "🔕 Выключить уведомления"


async def auth_redirect_callback(request: Request) -> Response:
    """
    Callback for discourse auth. Redirected from Mirea Ninja with a param a ?payload=[the API KEY].
    """
    payload = request.query_params.get("payload")

    private_key: str = application.bot_data["private_key"]

    bot_deeplink_url = f"https://t.me/{application.bot.username}?start="
    deeplink_payload = "auth_result_{}"

    if not payload:
        return RedirectResponse(url=f"{bot_deeplink_url}{deeplink_payload.format(AuthResult.ERROR)}")

    payload = json.loads(decode_payload(payload, private_key))
    key, nonce = payload["key"], payload["nonce"]

    user = await user_service.get_by_discourse_nonce(nonce)

    if not user:
        return RedirectResponse(url=f"{bot_deeplink_url}{deeplink_payload.format(AuthResult.ERROR)}")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{get_settings().DISCOURSE_URL}/session/current.json",
            headers={"User-Api-Key": key},
        )

        if response.status_code != 200:
            return RedirectResponse(url=f"{bot_deeplink_url}{deeplink_payload.format(AuthResult.ERROR)}")

        session = response.json()

    discourse_id = session["current_user"]["id"]

    if await user_service.get_by_discourse_id(discourse_id):
        return RedirectResponse(url=f"{bot_deeplink_url}{deeplink_payload.format(AuthResult.ACCOUNT_ALREADY_LINKED)}")

    await user_service.update_discourse_data(user.id, discourse_id, key)

    return RedirectResponse(url=f"{bot_deeplink_url}{deeplink_payload.format(AuthResult.SUCCESS)}")


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

    if "start_auth" in update.effective_message.text:
        await auth(update, context)
        return

    if "auth_result" not in update.effective_message.text:
        return

    deeplink_auth_result = int(update.effective_message.text.split("_")[-1])
    deeplink_auth_result = AuthResult(deeplink_auth_result)

    if deeplink_auth_result == AuthResult.ERROR:
        await update.effective_message.reply_text("❌ Произошла ошибка при авторизации. Попробуйте еще раз.")

    elif deeplink_auth_result == AuthResult.SUCCESS:
        logger.info("User %s has successfully authenticated", user.id)

        notifications_reply_markup = ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton(text=ENABLE_NOTIFICATIONS_MESSAGE),
                ],
            ],
            resize_keyboard=True,
        )

        await update.effective_message.reply_text(
            "✅ Аккаунт успешно привязан!\n\n"
            "Теперь вы можете получать уведомления о новых сообщениях на форуме прямо в Telegram.",
            reply_markup=notifications_reply_markup,
        )

    elif deeplink_auth_result == AuthResult.ACCOUNT_ALREADY_LINKED:
        logger.info("User %s has already authenticated", user.id)
        await update.effective_message.reply_text("❌ Этот аккаунт Mirea Ninja уже привязан к боту.")


async def auth(update: Update, context: CallbackContext) -> None:
    if not get_settings().RUN_WITH_WEBHOOK:
        await update.effective_message.reply_text(
            "❌ Бот не поддерживает в данный момент авторизацию через команду /auth. \n\n"
            "Обратитесь к администратору для подробностей.",
        )
        return

    if update.effective_chat.type != ChatType.PRIVATE:
        button = InlineKeyboardButton("🔗 Перейти", url=f"https://t.me/{application.bot.username}?start=start_auth")
        keyboard = InlineKeyboardMarkup([[button]])
        msg = await update.effective_message.reply_text(
            "Аутентификация доступна только в личных сообщениях бота.", reply_markup=keyboard
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

        response = await client.get(
            f"{get_settings().DISCOURSE_URL}/admin/users/{user.discourse_id}.json", headers=headers
        )

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
            f"👤 Информация о пользователе {data['username']}:\n\n"
            f"📅 Дата регистрации: {created_at_text}\n"
            f"📊 Количество сообщений: {data['post_count']}\n"
            f"📈 Количество лайков: {data['like_count']}\n"
            f"📊 Уровень доверия: {data['trust_level']}\n"
            f"{admin_text} {moderator_text}"
        )

        await msg.reply_text(text)


async def notifications(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    user = await user_service.get_by_id(update.effective_user.id)

    if not user:
        return

    if not user.discourse_id:
        await msg.reply_text("❌ Вы не привязали свой аккаунт к боту. Используйте /auth.")
        return

    if msg.text == ENABLE_NOTIFICATIONS_MESSAGE:
        await user_service.set_discourse_notifications_enabled(user.id, True)
        await msg.reply_text("✅ Уведомления включены.", reply_markup=ReplyKeyboardRemove())
    elif msg.text == DISABLE_NOTIFICATIONS_MESSAGE:
        await user_service.set_discourse_notifications_enabled(user.id, False)
        await msg.reply_text("✅ Уведомления выключены.", reply_markup=ReplyKeyboardRemove())


async def notifications_settings(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type != ChatType.PRIVATE:
        msg = await update.effective_message.reply_text("❌ Эта команда доступна только в личных сообщениях.")
        auto_delete(msg, context, from_message=update.effective_message)
        return

    msg = update.effective_message
    user = await user_service.get_by_id(update.effective_user.id)

    if not user:
        return

    if not user.discourse_id:
        await msg.reply_text("❌ Вы не привязали свой аккаунт к боту. Используйте /auth.")
        return

    if user.discourse_notifications_enabled:
        text = "✅ Уведомления включены."
    else:
        text = "❌ Уведомления выключены."

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(ENABLE_NOTIFICATIONS_MESSAGE)],
            [KeyboardButton(DISABLE_NOTIFICATIONS_MESSAGE)],
        ],
        resize_keyboard=True,
    )

    await msg.reply_text(text, reply_markup=keyboard)


application.add_handler(
    MessageHandler(
        filters.ChatType.PRIVATE
        & filters.TEXT
        & (filters.Regex(ENABLE_NOTIFICATIONS_MESSAGE) | filters.Regex(DISABLE_NOTIFICATIONS_MESSAGE)),
        notifications,
    )
)
application.add_handler(CommandHandler("notifications", notifications_settings), group=1)
application.add_handler(CommandHandler("start", auth_deeplink_callback), group=1)
application.add_handler(CommandHandler(["auth", "connect", "link"], auth), group=1)
application.add_handler(CommandHandler("whois", whois), group=1)
