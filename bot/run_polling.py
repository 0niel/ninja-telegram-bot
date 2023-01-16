from telegram import Update

from . import application


def run() -> None:
    application.run_polling(allowed_updates=Update.ALL_TYPES)
