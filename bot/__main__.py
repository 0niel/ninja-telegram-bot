import asyncio
import html
import json
import logging
import traceback

import uvicorn
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot import config, handlers, web_app
from bot.services import daily_job

from . import application

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
    await context.bot.send_message(
        chat_id=config.get_settings().MIREA_NINJA_GROUP_ID, text=message, parse_mode=ParseMode.HTML
    )


async def telegram(request: Request):
    """Handle incoming Telegram updates by putting them into the `update_queue`"""
    await application.update_queue.put(Update.de_json(data=await request.json(), bot=application.bot))
    return Response(status_code=200)


async def health(request: Request):
    return JSONResponse({"status": "ok"})


async def main() -> None:
    """Start the bot."""
    await application.bot.set_webhook(url=f"{config.get_settings().HOST}/telegram")

    # Set up webserver
    web_app.add_route("/telegram", telegram, methods=["POST"])
    web_app.add_route("/health", health, methods=["GET"])

    # Setup command and message handlers
    handlers.setup()

    # Register the error handler
    application.add_error_handler(error_handler)

    # Setup daily notification job
    daily_job.setup(application.job_queue)

    server = uvicorn.Server(config=uvicorn.Config(web_app, host="0.0.0.0", port=config.get_settings().PORT))

    # Run the bot
    async with application:
        await application.start()
        await server.serve()
        await application.idle()


if __name__ == "__main__":
    asyncio.run(main())
