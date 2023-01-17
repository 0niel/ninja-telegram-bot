import logging

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.helpers import escape_markdown

from bot import application
from bot.filters import IsChatAllowedFilter
from bot.services import user
from bot.services.auto_delete import auto_delete

logger = logging.getLogger(__name__)


async def on_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await user.update_user_names(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name,
        update.effective_user.last_name,
    )

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
        escape_markdown(
            f"@{update.effective_user.username} ({update.effective_user.first_name}) покинул нас. Надеемся, что мы "
            f"увидимся снова!",
            version=2,
        )
    )


# On join handler
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS & IsChatAllowedFilter(), on_join), group=3)

# On left handler
application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER & IsChatAllowedFilter(), on_left), group=3)
