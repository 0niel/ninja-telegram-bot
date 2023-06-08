import asyncio
import html
import json
import logging
import os
import traceback

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot import config
from bot import handlers
from bot.services import daily_job
from bot.utils import user_api_keys

from . import app_dir
from . import application
from . import run_polling as polling
from . import run_webhooks as webhooks

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"Возникло исключение во время обработки обновления.\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(chat_id=config.get_settings().ALLOWED_CHATS, text=message, parse_mode=ParseMode.HTML)


def init_keys() -> None:
    # Generate RSA key pair for Mirea Ninja Forum integration
    secure_dir = os.path.join(app_dir, "secure")

    if not os.path.exists(os.path.join(secure_dir, "private.key")) or not os.path.exists(
        os.path.join(secure_dir, "public.key")
    ):
        logger.info("Generating RSA key pair for Mirea Ninja Forum integration...")
        keys = user_api_keys.generate_rsa_keys()
        public_key, private_key = keys["public"], keys["private"]

        with open(os.path.join(secure_dir, "private.key"), "wb") as private_key_file:
            private_key_file.write(private_key.encode())

        with open(os.path.join(secure_dir, "public.key"), "wb") as public_key_file:
            public_key_file.write(public_key.encode())

    else:
        logger.info("RSA key pair for Mirea Ninja Forum integration exists. Cool!")
        with open(os.path.join(secure_dir, "private.key"), "rb") as private_key_file:
            private_key = private_key_file.read().decode()

        with open(os.path.join(secure_dir, "public.key"), "rb") as public_key_file:
            public_key = public_key_file.read().decode()

    application.bot_data["private_key"] = private_key
    application.bot_data["public_key"] = public_key


def setup() -> None:
    """Setup the bot."""

    # Init RSA keys
    init_keys()

    # Setup command and message handlers
    handlers.setup()

    # Register the error handler
    # application.add_error_handler(error_handler)

    # Setup daily notification job
    daily_job.setup(application.job_queue)


if __name__ == "__main__":
    setup()

    if config.get_settings().RUN_WITH_WEBHOOK:
        asyncio.run(webhooks.run())
    else:
        polling.run()
