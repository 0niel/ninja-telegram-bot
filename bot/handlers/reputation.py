import logging
from telegram import ParseMode, Update
from telegram.utils.helpers import escape_markdown
from telegram.ext import CallbackContext
from telegram_bot_pagination import InlineKeyboardPaginator

from bot.filters.has_user_in_args import HasUserInArgsFilter
from bot.handlers.users import users_updater
from bot.models.reputation_update import ReputationUpdate
from bot.models.user import User
from bot.services.auto_delete import auto_delete
from bot.services.reputation import compute_force, compute_rep, get_rating

logger = logging.getLogger(__name__)
logs_data = []

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
                new_message = message.reply_text(
                    '❌ Репутацию можно изменять один раз в 10 минут!')
                auto_delete(new_message, context)
                return

        if ReputationUpdate.is_user_send_rep_to_message(from_user_id, message.reply_to_message.message_id):
            new_message = message.reply_text(
                '❌ Вы уже изменяли репутацию, используя это сообщение!')
            auto_delete(new_message, context)
            return

        reputation_change = context.reputation[0]['reputation_change']

        new_user_rep_delta = compute_rep(reputation_change, from_user.force)
        new_user_force_delta = compute_force(
            reputation_change, from_user.force)

        new_user_force = round(to_user.force + new_user_force_delta, 3)
        new_user_rep = round(to_user.reputation + new_user_rep_delta, 3)

        User.update_rep_and_force(
            from_user_id, to_user_id, new_user_rep, new_user_force)

        ReputationUpdate(message_id=message.reply_to_message.message_id, from_user_id=from_user_id, to_user_id=to_user_id, reputation_delta=new_user_rep_delta,
                         force_delta=new_user_force_delta, new_reputation=new_user_rep, new_force=new_user_force).create()

        from_username = message.from_user.first_name
        to_username = message.reply_to_message.from_user.first_name

        new_user_rep_delta = round(new_user_rep_delta, 3)
        new_rep = '+' + \
            str(new_user_rep_delta) if new_user_rep_delta > 0 else str(
                new_user_rep_delta)

        icon = '👎' if reputation_change < 0 else '👍'

        logger.info(
            f'{from_username} has updated {to_username} reputation {new_rep}')

        new_message = context.bot.send_message(message.chat_id,
                                               f"{icon} *{from_username}* ({from_user.reputation}, {from_user.force}) "
                                               f"обновил(а) вам репутацию ({new_rep})",
                                               reply_to_message_id=message.reply_to_message.message_id, parse_mode=ParseMode.MARKDOWN)
        auto_delete(new_message, context)


def show_leaders_callback(update: Update, context: CallbackContext) -> None:
    new_message = update.effective_message.reply_text(
        get_rating(User.get_by_rating(15)), parse_mode=ParseMode.MARKDOWN)

    auto_delete(new_message, context, from_message=update.effective_message)


def show_self_rating_callback(update: Update, context: CallbackContext) -> None:
    user = User.get(update.effective_message.from_user.id)

    new_message = update.effective_message.reply_text(update.effective_message.from_user.first_name +
                                                      ', у вас {} рейтинга и {} очков влияния'.format(user.reputation, user.force))

    auto_delete(new_message, context, from_message=update.effective_message)


def about_user_callback(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message

    if msg.reply_to_message:
        from_user_id = msg.reply_to_message.from_user.id
        user = User.get(from_user_id)
    elif HasUserInArgsFilter().filter(msg):
        username = context.args[0].replace('@', '').strip()
        user = User.get_by_username(username)
    else:
        new_message = msg.reply_text(
            '❌ Вы должны ответить на сообщение пользователя или упомянуть его!')
        auto_delete(new_message, context, from_message=msg)
        return

    if user:
        new_message = update.effective_message.reply_text(
            'Пользователь {} имеет {} рейтинга и {} очков влияния'.format(user.first_name, user.reputation, user.force))
    else:
        new_message = update.effective_message.reply_text(
            'Пользователь {} имеет 0.0 рейтинга и 0.0 очков влияния'.format(user.first_name))

    auto_delete(new_message, context, from_message=msg)


def reputation_history_callback(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message

    history = ReputationUpdate.get_history(msg.from_user.id)

    logs_data = []
    logs_text = ''

    if history:
        for i in range(len(history)):
            from_user = User.get(history[i].from_user_id)
            updated_at = str(history[i].updated_at).split('.')[0]
            updated_at_date = escape_markdown(updated_at.split()[0], version=2)
            updated_at_time = escape_markdown(updated_at.split()[1], version=2)

            # round it up so as not to show too large numbers
            history[i].reputation_delta = round(history[i].reputation_delta, 3)
            history[i].force_delta = round(history[i].force_delta, 3)

            new_rep = escape_markdown('+' +
                                      str(history[i].reputation_delta) if history[i].reputation_delta > 0 else str(
                                          history[i].reputation_delta), version=2)

            new_force = escape_markdown('+' +
                                        str(history[i].force_delta) if history[i].force_delta > 0 else str(
                                            history[i].force_delta), version=2)

            new_rep = escape_markdown(
                str(history[i].new_reputation), version=2)

            index = str(i + 1)

            if i % 10 is not 0 or i is 0:
                logs_text += f'{index}\. *{from_user.first_name}* изменил\(а\) репутацию {updated_at_date} в {updated_at_time} \({new_rep}; {new_force}\)\. Новая репутация: _{new_rep}_\n'
            else:
                logs_data.append(logs_text)
                logs_text = ''
        
        if logs_text is not '':
            logs_data.append(logs_text)

        paginator = InlineKeyboardPaginator(len(logs_data), data_pattern='logs#{page}')
        new_message = msg.reply_html(text=logs_data[0], reply_markup=paginator.markup, parse_mode=ParseMode.MARKDOWN_V2)

    else:
        new_message = msg.reply_text(
            '❌ У вас ещё нет истории изменения репутации.')

    auto_delete(new_message, context, from_message=msg)


def reputation_history_page_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    page = int(query.data.split('#')[1])
    paginator = InlineKeyboardPaginator(
        len(logs_data), current_page=page, data_pattern='logs#{page}')
    query.edit_message_text(
        text=logs_data[page - 1], reply_markup=paginator.markup)
