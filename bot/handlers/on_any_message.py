import datetime

from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler
from telegram.ext import filters

from bot import application
from bot import timezone_offset
from bot.filters import IsChatAllowedFilter
from bot.services import messages_history
from bot.services import user


async def users_updater(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if msg is None:
        return

    # Update default user info
    await user.update_user_names(
        msg.from_user.id,
        msg.from_user.username,
        msg.from_user.first_name,
        msg.from_user.last_name,
    )

    # Increment user messages count
    await messages_history.add_message(
        msg.from_user.id,
        datetime.datetime.now(timezone_offset).date(),
    )

    # Update user info from reply
    if msg.reply_to_message:
        await user.update_user_names(
            msg.reply_to_message.from_user.id,
            msg.reply_to_message.from_user.username,
            msg.reply_to_message.from_user.first_name,
            msg.reply_to_message.from_user.last_name,
        )

    # Update user info from forward
    if msg.forward_from:
        await user.update_user_names(
            msg.forward_from.id,
            msg.forward_from.username,
            msg.forward_from.first_name,
            msg.forward_from.last_name,
        )


application.add_handler(
    MessageHandler(
        filters.ALL & IsChatAllowedFilter(),
        users_updater,
    ),
    group=5,
)
