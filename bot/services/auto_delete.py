import re

from telegram import Message
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot import config

DELETE_MESSAGE_TEMPLATE = "Это системное сообщение будет удалено через {seconds} секунд..."


def get_message_parse_mode(text: str) -> ParseMode:
    """Returns formatting type of message."""
    if re.search(r"<\w+>|</\w+>", text):
        return ParseMode.HTML

    # By default, telegram uses markdown formatting.
    return ParseMode.MARKDOWN_V2


async def edit_message_repeating_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    message: Message = context.job.data["message"]
    time_to_delete: int = context.job.data["time_to_delete"]

    if message.reply_markup:
        return

    if time_left := re.search(DELETE_MESSAGE_TEMPLATE.format(seconds=r"(?P<seconds>\d+)"), message.text):
        time_left = int(time_left["seconds"])
        message = await message.edit_text(
            message.text.replace(
                DELETE_MESSAGE_TEMPLATE.format(seconds=time_left), DELETE_MESSAGE_TEMPLATE.format(seconds=time_left - 5)
            ),
            parse_mode=get_message_parse_mode(message.text),
        )
    else:
        message = await message.edit_text(
            message.text + "\n\n" + DELETE_MESSAGE_TEMPLATE.format(seconds=time_to_delete),
            parse_mode=get_message_parse_mode(message.text),
        )

    context.job.data["message"] = message


async def delete_message_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    message: Message = context.job.data

    await message.delete()


def auto_delete(
    message: Message, context: ContextTypes.DEFAULT_TYPE, from_message: Message = None, delete_after: int = 45
) -> None:
    """Auto-deletion of the bot message after a certain time."""
    if message.chat.id in config.get_settings().ALLOWED_CHATS or len(config.get_settings().ALLOWED_CHATS) == 0:
        context.job_queue.run_repeating(
            edit_message_repeating_callback,
            interval=5,
            first=-5,
            last=delete_after,
            name=f"edit_message_repeating_callback_{message.message_id}",
            data={"message": message, "time_to_delete": delete_after},
        )

        context.job_queue.run_once(
            delete_message_callback,
            delete_after + 5,
            name=f"delete_message_callback_{message.message_id}",
            data=message,
        )

        if from_message:
            context.job_queue.run_once(
                delete_message_callback,
                delete_after + 5,
                name=f"delete_message_callback_{from_message.message_id}",
                data=from_message,
            )
