import uvicorn
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response
from telegram import Update

from bot import config

from . import application

if config.get_settings().RUN_WITH_WEBHOOK:
    from . import web_app


async def telegram(request: Request):
    """Handle incoming Telegram updates by putting them into the `update_queue`"""
    await application.update_queue.put(Update.de_json(data=await request.json(), bot=application.bot))
    return Response(status_code=200)


async def health(request: Request):
    return JSONResponse({"status": "ok"})


async def run() -> None:
    """Start the bot."""
    if config.get_settings().RUN_WITH_WEBHOOK:
        await application.bot.set_webhook(url=f"{config.get_settings().HOST}/telegram")

        # Set up webserver
        web_app.add_route("/telegram", telegram, methods=["POST"])
        web_app.add_route("/health", health, methods=["GET"])

    # Run the bot
    if config.get_settings().RUN_WITH_WEBHOOK:
        server = uvicorn.Server(config=uvicorn.Config(web_app, host="0.0.0.0", port=config.get_settings().PORT))

        async with application:
            await application.start()
            await server.serve()
            await application.stop()
