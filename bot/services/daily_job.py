import datetime
import random

import pytz
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.ext import JobQueue

from bot import config
from bot import timezone_offset
from bot.services import messages_history
from bot.services import user as user_service
from bot.utils.plural_forms import get_plural_forms

NEW_FORCES = {0: 1.2, 1: 1, 2: 0.8, 3: 0.8, 4: 0.8}


async def daily_job(context: ContextTypes.DEFAULT_TYPE):
    top_by_messages = await messages_history.get_top_by_date(datetime.datetime.now(timezone_offset).date())

    text = "👑 Итоги дня! Самые активные пользователи получают дополнительные очки влияния.\n\n"

    for i in range(len(top_by_messages)):
        chat_member = await context.bot.get_chat_member(
            config.get_settings().ALLOWED_CHATS, top_by_messages[i].user_id
        ).user

        user = await user_service.get_by_id(top_by_messages[i].user_id)

        new_force = NEW_FORCES[i]

        await user_service.update_force(user.id, user.force + new_force)

        suffix = ["сообщение", "сообщения", "сообщений"][get_plural_forms(top_by_messages[i].messages)]

        text += (
            f"<b>{top_by_messages[i].messages}</b> {suffix} от {chat_member.first_name}, "
            f"<i>+{new_force} влияния</i>\n"
        )

    await context.bot.send_message(chat_id=config.get_settings().ALLOWED_CHATS, text=text, parse_mode=ParseMode.HTML)


async def daily_weather_job(context: ContextTypes.DEFAULT_TYPE):
    text = "Доброе утро!\n\n" "<b>Погода на сегодня:</b>\n"

    images_url = "https://raw.githubusercontent.com/0niel/happy-new-day/main/images/{}.jpg"

    await context.bot.send_photo(
        chat_id=config.get_settings().ALLOWED_CHATS,
        photo=images_url.format(random.randint(1, 1500)),
        caption=text,
        parse_mode=ParseMode.HTML,
    )


def setup(job_queue: JobQueue):
    """Setup daily notification job"""
    t = datetime.time(23, 59, 00, 000000, tzinfo=pytz.timezone("Europe/Moscow"))

    t2 = datetime.time(5, 45, 00, 000000, tzinfo=pytz.timezone("Europe/Moscow"))

    job_queue.run_daily(daily_job, t)
    job_queue.run_daily(daily_weather_job, t2)
