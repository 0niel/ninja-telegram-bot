from telegram import Message
from telegram.ext import CallbackContext

from bot import config


def auto_delete_callback(context: CallbackContext) -> None:
    context.job.context.delete()


def auto_delete(
    message: Message, context: CallbackContext, from_message=None, seconds=45
) -> None:
    """Auto-deletion of the bot message after 45 seconds

    Args:
        message (Message): the bot's message to delete
        context (CallbackContext): message context
        from_message (_type_, optional): the command that triggered the bot
        message if it needs to be deleted too. Defaults to None.
    """
    if message.chat.id == config.MIREA_NINJA_GROUP_ID:
        context.job_queue.run_once(auto_delete_callback, seconds, context=message)

        if from_message:
            context.job_queue.run_once(
                auto_delete_callback, seconds, context=from_message
            )
