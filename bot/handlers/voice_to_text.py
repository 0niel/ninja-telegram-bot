import asyncio

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot import application
from bot.services import voice_to_text as voice_to_text


async def on_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message

    new_msg = await msg.reply_text("Распознаю текст...")

    new_file = await msg.voice.get_file()
    file_name = "files\\" + msg.voice.file_unique_id + ".ogg"
    await new_file.download_to_drive(file_name)

    loop = asyncio.get_event_loop()
    text = await loop.run_in_executor(None, voice_to_text.run, file_name)
    if text:
        await new_msg.edit_text("Текст аудио:\n\n" + text)
    else:
        await new_msg.edit_text("🤷‍♂️ Мне не удалось распознать текст." + text)


application.add_handler(
    MessageHandler(filters.VOICE & filters.ChatType.GROUPS, on_voice_message),
)
