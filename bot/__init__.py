import logging
from datetime import timedelta
from datetime import timezone
from pathlib import Path

from telegram.ext import Application

from . import config

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


app_dir: Path = Path(__file__).parent.parent

timezone_offset = timezone(timedelta(hours=3))

# Create the Application and pass it bot's token.
if config.get_settings().RUN_WITH_WEBHOOK:
    from fastapi import FastAPI

    application = Application.builder().token(config.get_settings().TELEGRAM_TOKEN).updater(None).build()
    web_app = FastAPI()
else:
    application = Application.builder().token(config.get_settings().TELEGRAM_TOKEN).build()
