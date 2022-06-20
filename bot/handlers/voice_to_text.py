from telegram import Update
from telegram.ext import CallbackContext

from bot.services import voice_to_text as voice_to_text


def voice_to_text_callback(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message

    new_msg = msg.reply_text("Распознаю текст...")

    new_file = msg.voice.get_file()
    file_name = "files\\" + msg.voice.file_unique_id + ".ogg"
    new_file.download(file_name)

    text = voice_to_text.run(file_name)

    if text:
        new_msg.edit_text("Текст аудио:\n\n" + text)
    else:
        new_msg.edit_text("🤷‍♂️ Мне не удалось распознать текст." + text)