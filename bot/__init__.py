import logging

from datetime import timedelta, timezone
from pathlib import Path

from telegram.ext import Application

from . import config

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


app_dir: Path = Path(__file__).parent.parent

timezone_offset = timezone(timedelta(hours=3))

# Create the Application and pass it bot's token.
application = Application.builder().token(config.get_settings().TELEGRAM_TOKEN).build()
