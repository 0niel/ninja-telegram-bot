import logging
from pathlib import Path

from telegram.ext import Updater

from . import config

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

app_dir: Path = Path(__file__).parent.parent

# Create the Updater and pass it your bot's token.
updater = Updater(config.TELEGRAM_TOKEN, use_context=True)

# Get the dispatcher to register handlers
dispatcher = updater.dispatcher
