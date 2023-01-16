import logging

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot import application, config
from bot.services import user

logger = logging.getLogger(__name__)


async def on_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != config.get_settings().MIREA_NINJA_GROUP_ID:
        return

    await user.update_user_names(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name,
        update.effective_user.last_name,
    )

    guidelines_url = "https://mirea.ninja/guidelines"
    title = update.effective_chat.title

    await update.message.reply_markdown_v2(
        f"Спасибо, что присоединились к {title}, и Добро пожаловать!\n\n"
        f"Этот чат управляется нашим дружелюбным персоналом и вами - сообществом.\n\n"
        f"Если есть критическая или срочная проблема, пожалуйста, свяжитесь с нами в личных сообщениях.\n\n"
        f"- Мы всегда следуем [основным принципам сообщества]({guidelines_url})."
    )


async def on_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != config.get_settings().MIREA_NINJA_GROUP_ID:
        return

    await update.message.reply_markdown_v2(
        f"{update.effective_user.first_name} покинул нас. Надеемся, что мы увидимся снова!"
    )


# On join handler
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_join), group=2)

# On left handler
application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, on_left), group=3)
