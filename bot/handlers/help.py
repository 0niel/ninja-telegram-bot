from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler

from bot import application
from bot.services.auto_delete import auto_delete


async def help_callback(update: Update, context: CallbackContext) -> None:
    new_message = await update.effective_message.reply_text(
        "- Система репутации:\n"
        "*Репутация* - это основной показатель вашего рейтинга. Чем выше репутация, тем больше вклада вы внесли в "
        "общение в беседе Mirea Ninja.\n\n "
        "*Влияние* - это показатель того, насколько ваш голос силен. Сила набирается вслед за репутацией, "
        "но не снижается вместе с ней.",
        parse_mode=ParseMode.MARKDOWN,
    )

    auto_delete(new_message, context, from_message=update.effective_message)


# show brief information about the bot
application.add_handler(CommandHandler("help", help_callback))
