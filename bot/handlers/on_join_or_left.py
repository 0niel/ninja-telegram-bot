import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler
from telegram.ext import filters
from telegram.helpers import escape_markdown

from bot import application
from bot.filters import IsChatAllowedFilter
from bot.handlers.on_any_message import users_updater
from bot.services.auto_delete import auto_delete

logger = logging.getLogger(__name__)


async def on_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await users_updater(update, context)

    guidelines_url = "https://mirea.ninja/guidelines"
    title = update.effective_chat.title

    msg = await update.message.reply_html(
        f"Спасибо, что присоединились к {title}, и Добро пожаловать!\n\n"
        f"Этот чат управляется нашим дружелюбным персоналом и вами - сообществом.\n\n"
        f"Если есть критическая или срочная проблема, пожалуйста, свяжитесь с нами в личных сообщениях.\n\n"
        f"- Мы всегда следуем <a href='{guidelines_url}'>основным принципам сообщества</a>.\n"
    )

    auto_delete(msg, context)


async def on_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=escape_markdown(
            f"@{update.effective_user.username} ({update.effective_user.first_name}) покинул(а) нас. Надеемся, что мы "
            f"увидимся снова!",
            version=2,
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


# On join handler
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS & IsChatAllowedFilter(), on_join), group=3)

# On left handler
application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER & IsChatAllowedFilter(), on_left), group=3)
