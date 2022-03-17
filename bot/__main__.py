import logging
from pathlib import Path
from telegram.ext import Updater

from . import config

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

app_dir: Path = Path(__file__).parent.parent


def main() -> None:
    """Start the bot."""
    from bot import handlers

    # Create the Updater and pass it your bot's token.
    updater = Updater(config.TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Setup command and message handlers
    handlers.setup(dispatcher)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
