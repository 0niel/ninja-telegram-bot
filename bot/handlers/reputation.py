import logging
from bot import config
from telegram import Message, ParseMode, Update
from telegram.ext import CallbackContext
from bot.handlers.users import users_updater
from bot.models.reputation_update import ReputationUpdate
from bot.models.user import User
from bot.services.auto_delete import auto_delete


from bot.services.reputation import compute_force, compute_rep, get_rating

logger = logging.getLogger(__name__)


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
        get_rating(User.get_by_rating()), parse_mode=ParseMode.MARKDOWN)

    auto_delete(new_message, context, from_message=update.effective_message)


def show_self_rating_callback(update: Update, context: CallbackContext) -> None:
    user = User.get(update.effective_message.from_user.id)

    new_message = update.effective_message.reply_text(update.effective_message.from_user.first_name +
                                                      ', у вас {} рейтинга и {} очков влияния'.format(user.reputation, user.force))

    auto_delete(new_message, context, from_message=update.effective_message)


def about_rating_callback(update: Update, context: CallbackContext) -> None:
    new_message = update.effective_message.reply_text(
        '*Репутация* - это основной показатель вашего рейтинга. Чем выше репутация, тем больше вклада вы внесли в общение в беседе Mirea Ninja.\n\n*Влияние* - это показатель того, насколько ваш голос силен. Сила набирается вслед за репутацией, но не снижается вместе с ней.', parse_mode=ParseMode.MARKDOWN)

    auto_delete(new_message, context, from_message=update.effective_message)
