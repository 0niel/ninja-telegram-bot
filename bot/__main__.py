import bot.services.daily_job as daily_job
from bot import handlers

from . import updater


def main() -> None:
    """Start the bot."""

    # Setup command and message handlers
    handlers.setup()

    # Setup daily notification job
    daily_job.setup(updater.job_queue)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
