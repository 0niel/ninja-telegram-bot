import re

from telegram import Message
from telegram.ext import ContextTypes

from bot import config

DELETE_MESSAGE_TEMPLATE = "Это системное сообщение будет удалено через {seconds} секунд..."


async def edit_message_repeating_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    message: Message = context.job.data["message"]
    time_to_delete: int = context.job.data["time_to_delete"]

    if message.reply_markup:
        return

    if time_left := re.search(r"\d+", message.text):
        time_left = int(time_left[0])
        message = await message.edit_text(
            message.text.replace(
                DELETE_MESSAGE_TEMPLATE.format(seconds=time_left), DELETE_MESSAGE_TEMPLATE.format(seconds=time_left - 5)
            ),
        )
    else:
        message = await message.edit_text(
            message.text + "\n\n" + DELETE_MESSAGE_TEMPLATE.format(seconds=time_to_delete),
        )

    context.job.data["message"] = message


async def delete_message_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    message: Message = context.job.data

    await message.delete()


def auto_delete(
    message: Message, context: ContextTypes.DEFAULT_TYPE, from_message: Message = None, delete_after: int = 45
) -> None:
    """Auto-deletion of the bot message after a certain time."""
    if message.chat.id == config.get_settings().MIREA_NINJA_GROUP_ID:
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
