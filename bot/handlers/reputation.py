import logging
import math
from telegram import ForceReply, ParseMode, Update
from telegram.utils.helpers import escape_markdown
from telegram.ext import CallbackContext
from bot.handlers.users import users_updater
from bot.models.user import User
import sqlalchemy as sa

logger = logging.getLogger(__name__)


def compute_force(rep, force):
    i_min_size = 0.1
    i_max_size = 8

    size_range = i_max_size-i_min_size

    i_min_count = math.log(0+1)
    i_max_count = math.log(500+1)

    i_count_range = i_max_count-i_min_count

    if i_count_range == 0:
        i_count_range = 1

    if force > 50 and force < 200:
        force_new = force / 70
    elif force >= 200:
        force_new = force / 10
    else:
        force_new = force / 100

    delta = i_min_size + (math.log(force_new + 1) - i_min_count) * \
        (size_range / i_count_range)

    new_force_delta = rep * delta
    new_force_delta = 0 if new_force_delta < 0 else new_force_delta

    return new_force_delta


def compute_rep(rep, force):
    i_min_size = 0.5
    i_max_size = 15

    size_range = i_max_size-i_min_size

    i_min_count = math.log(0+1)
    i_max_count = math.log(500+1)

    i_count_range = i_max_count-i_min_count

    if i_count_range == 0:
        i_count_range = 1

    if force > 50 and force < 200:
        force_new = force / 20
    elif force >= 200:
        force_new = force / 10
    else:
        force_new = force / 50

    delta = i_min_size+(math.log(force_new+1) - i_min_count) * \
        (size_range / i_count_range)

    return rep * delta


def reputation_callback(update: Update, context: CallbackContext) -> None:
    if context.reputation:
        message = update.effective_message

        from_user_id = message.from_user.id
        to_user_id = message.reply_to_message.from_user.id

        from_user = User.get(from_user_id)
        to_user = User.get(to_user_id)

        if from_user is None or to_user is None:
            users_updater(update, context)
            from_user = User.get(from_user_id)
            to_user = User.get(to_user_id)

        if from_user.update_reputation_at:
            if from_user.is_rep_change_available() is False:
                message.reply_text(
                    '❌ Репутацию можно изменять один раз в 10 минут!')
                return

        reputation_change = context.reputation[0]['reputation_change']

        new_user_rep_delta = compute_rep(reputation_change, from_user.force)
        new_user_force_delta = compute_force(
            reputation_change, from_user.force)

        new_user_force = round(to_user.force + new_user_force_delta, 3)
        new_user_rep = round(to_user.reputation + new_user_rep_delta, 3)

        User.update_rep_and_force(
            from_user_id, to_user_id, new_user_rep, new_user_force)

        from_username = message.from_user.first_name
        to_username = message.reply_to_message.from_user.first_name

        new_user_rep_delta = round(new_user_rep_delta, 3)
        new_rep = '+' + \
            str(new_user_rep_delta) if new_user_rep_delta > 0 else str(
                new_user_rep_delta)

        icon = '👎' if reputation_change < 0 else '👍'

        context.bot.send_message(message.chat_id,
                                 f"{icon} *{from_username}* ({from_user.reputation}, {from_user.force}) "
                                 f"обновил(а) вам репутацию ({new_rep})",
                                 reply_to_message_id=message.reply_to_message.message_id, parse_mode=ParseMode.MARKDOWN)


def show_leaders_callback(update: Update, context: CallbackContext) -> None:
    users = User.get_by_rating()

    if len(users) == 0:
        update.effective_message.reply_text(
            'На данный момент нет активных участников для формирования рейтинга')
        return

    medals = {0: '🥇', 1: '🥈', 2: '🥉'}

    lines = []
    for i in range(len(users)):
        medal = ''
        if i in medals:
            medal = medals[i]

        lines.append(str(i+1) + '. {} - {} репутации и {} влияния {}'.format(
            users[i].first_name + ' ' +
            users[i].last_name if users[i].last_name is not None else users[i].first_name,
            users[i].reputation if users[i].reputation >= 0 else f'({users[i].reputation})', users[i].force, medal))

    update.effective_message.reply_text(
        '*Рейтинг:*\n' + escape_markdown('\n'.join(lines)), parse_mode=ParseMode.MARKDOWN)


def show_self_rating_callback(update: Update, context: CallbackContext) -> None:
    user = User.get(update.effective_message.from_user.id)

    update.effective_message.reply_text(update.effective_message.from_user.first_name +
                                        ', у вас {} рейтинга и {} очков влияния'.format(user.reputation, user.force))


def about_rating_callback(update: Update, context: CallbackContext) -> None:
    update.effective_message.reply_text(
        '*Репутация* - это основной показатель вашего рейтинга. Чем выше репутация, тем больше вклада вы внесли в общение в беседе Mirea Ninja.\n\n*Влияние* - это показатель того, насколько ваш голос силен. Сила набирается вслед за репутацией, но не снижается вместе с ней.', parse_mode=ParseMode.MARKDOWN)
