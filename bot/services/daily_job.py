import datetime
import pytz
from telegram import ParseMode
from telegram.ext import JobQueue
from telegram.utils.helpers import escape_markdown
from bot import config
from bot.models.messages_history import MessagesHistory
from bot.models.user import User


offset = datetime.timezone(datetime.timedelta(hours=3))

NEW_FORCES = {0: 1.2, 1: 1, 2: 0.8, 3: 0.8, 4: 0.8}


def daily_job(context):
    top_by_messages = MessagesHistory.get(datetime.datetime.now(offset).date())

    text = '👑 Итоги дня\! Самые активные пользователи получают дополнительные очки влияния\.\n\n'

    for i in range(len(top_by_messages)):
        chat_member = context.bot.get_chat_member(
            config.MIREA_NINJA_GROUP_ID, top_by_messages[i].user_id).user

        user = User.get(top_by_messages[i].user_id)

        if user is None:
            User.update(chat_member.id, chat_member.username,
                        chat_member.first_name, chat_member.last_name)
            user = User.get(top_by_messages[i].user_id)

        new_force = NEW_FORCES[i]

        User.update_force(user.id, user.force + new_force)

        text += f'*{top_by_messages[i].messages}* сообщений от {chat_member.first_name}, _\+{escape_markdown(str(new_force), version=2)} влияния_\n'

    context.bot.send_message(
        chat_id=config.MIREA_NINJA_GROUP_ID, text=text, parse_mode=ParseMode.MARKDOWN_V2)


def setup(job_queue: JobQueue):
    """Setup daily notification job"""
    t = datetime.time(23, 59, 00, 000000, tzinfo=pytz.timezone(
        'Europe/Moscow'))

    job_queue.run_daily(daily_job, t)
