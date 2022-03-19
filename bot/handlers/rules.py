import logging
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from telegram.utils.helpers import escape_markdown

from bot.services.auto_delete import auto_delete


RULES_TEXT = (
    'Чат является важным средством коммуникации, но при чрезмерном использовании он '
    'может оказать негативное влияние на здоровье сообщества.'
    '\n\n'
    'Т.к. группа в телеграме является частью сообщества Mirea Ninja, в '
    'ней действуют те же правила, что и на форуме, но с некоторыми поправками на эфемерность:'
    '\n\n'
    '1. 😈 Можно материться. Обзываться и переходить на личности - нельзя.\n'
    '2. 👺 Анонимность != вседозволенность. Мы рекомендуем не подрывать учебный процесс и не нарушать законы РФ, используя этот чат.\n'
    '3. 👋 С новыми участниками у нас принято общаться на «ты» и относиться к ним как к друзьям. Будьте вежливы.\n'
    '4. 🤝 Прося что-то, давайте что-то взамен. Если вам помогли, не забудьте поставить +реп.\n'
    '5. 🚪 Это частная вечеринка. Если вы очень душный — вас выставляют за дверь. Тут нет демократии.'
)


def rules_callback(update: Update, context: CallbackContext) -> None:
    message = update.effective_message.reply_text(
        escape_markdown(RULES_TEXT, version=2).replace('рекомендуем', '_рекомендуем_'), parse_mode=ParseMode.MARKDOWN_V2)
    auto_delete(message, context, from_message=update.effective_message)
