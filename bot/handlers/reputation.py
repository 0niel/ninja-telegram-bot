import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
)
from telegram_bot_pagination import InlineKeyboardPaginator

from bot import dispatcher, config
from bot.filters.has_user_in_args import HasUserInArgsFilter
from bot.filters.reputation_change import ReputationChangeFilter
from bot.handlers.users import users_updater
from bot.models.reputation_update import ReputationUpdate
from bot.models.user import User
from bot.services.auto_delete import auto_delete
from bot.services.reputation import (
    compute_force,
    compute_rep,
    get_rating,
    get_rating_by_slice,
)

logger = logging.getLogger(__name__)


def reputation_callback(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    if context.reputation:
        error_message = None

        if message.chat.id != config.MIREA_NINJA_GROUP_ID:
            error_message = message.reply_text(
                "❌ Эта команда работает только в группе Mirea Ninja!"
            )
        elif not message.reply_to_message:
            # error_message = message.reply_text(
            #     "❌ Вы должны ответить на сообщение пользователя!"
            # )
            return
        elif message.from_user.is_bot:
            error_message = message.reply_text(
                "❌ Изменять репутацию может только пользователь!"
            )
        elif message.reply_to_message.from_user.id == message.from_user.id:
            error_message = message.reply_text(
                "❌ Вы не можете изменить репутацию самому себе!"
            )
        elif message.reply_to_message.from_user.is_bot:
            error_message = message.reply_text(
                "❌ Вы не можете изменить репутацию бота!"
            )

        if error_message:
            auto_delete(error_message, context)
            return

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
                    "❌ Репутацию можно изменять один раз в 10 минут!"
                )
                auto_delete(new_message, context)
                return

        if ReputationUpdate.is_user_send_rep_to_message(
            from_user_id, message.reply_to_message.message_id
        ):
            new_message = message.reply_text(
                "❌ Вы уже изменяли репутацию, используя это сообщение!"
            )
            auto_delete(new_message, context)
            return

        reputation_change = context.reputation[0]["reputation_change"]

        new_user_rep_delta = round(compute_rep(reputation_change, from_user.force), 5)
        new_user_force_delta = round(
            compute_force(reputation_change, from_user.force), 5
        )

        new_user_force = round(to_user.force + new_user_force_delta, 3)
        new_user_rep = round(to_user.reputation + new_user_rep_delta, 3)

        User.update_rep_and_force(
            from_user_id, to_user_id, new_user_rep, new_user_force
        )

        ReputationUpdate(
            message_id=message.reply_to_message.message_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            reputation_delta=new_user_rep_delta,
            force_delta=new_user_force_delta,
            new_reputation=new_user_rep,
            new_force=new_user_force,
        ).create()

        from_username = message.from_user.first_name
        to_username = message.reply_to_message.from_user.first_name

        new_user_rep_delta = round(new_user_rep_delta, 3)

        new_rep = (
            "+" + str(new_user_rep_delta)
            if new_user_rep_delta > 0
            else str(new_user_rep_delta)
        )

        icon = "👎" if reputation_change < 0 else "👍"

        logger.info(f"{from_username} has updated {to_username} reputation {new_rep}")

        new_message = context.bot.send_message(
            message.chat_id,
            f"{icon} *{from_username}* ({from_user.reputation:.3f}, {from_user.force:.3f}) "
            f"обновил(а) вам репутацию ({new_rep})",
            reply_to_message_id=message.reply_to_message.message_id,
            parse_mode=ParseMode.MARKDOWN,
        )
        auto_delete(new_message, context)


def show_leaders_callback(update: Update, context: CallbackContext) -> None:
    new_message = update.effective_message.reply_text(
        get_rating(User.get_by_rating(15)), parse_mode=ParseMode.MARKDOWN
    )

    auto_delete(new_message, context, from_message=update.effective_message)


def show_self_rating_callback(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_message.from_user.id
    user = User.get(user_id)

    keyboard = [
        [
            InlineKeyboardButton(
                "Показать позицию в рейтинге", callback_data=f"show_pos#{str(user_id)}"
            )
        ],
    ]

    new_message = update.effective_message.reply_text(
        "{}, у вас {} рейтинга и {} очков влияния".format(
            update.effective_message.from_user.first_name,
            f"{user.reputation:.3f}",
            f"{user.force:.3f}",
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    auto_delete(new_message, context, from_message=update.effective_message)


def show_self_rating_position_callback(
    update: Update, context: CallbackContext
) -> None:
    query = update.callback_query
    user_id = int(query.data.split("#")[1])
    if update.callback_query.from_user.id == user_id:
        rating_slice = User.get_rating_slice(user_id, 5, 5)

        if rating_slice:
            text = get_rating_by_slice(rating_slice, user_id)
            query.edit_message_text(text=text, parse_mode=ParseMode.MARKDOWN)
            query.answer()
        else:
            query.answer("Для вас ещё не сформировалась позиция в рейтинге")
    else:
        query.answer("Вы не можете пользоваться данной клавиатурой")


def about_user_callback(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message

    if msg.reply_to_message:
        from_user_id = msg.reply_to_message.from_user.id
        user = User.get(from_user_id)
    elif HasUserInArgsFilter().filter(msg):
        username = context.args[0].replace("@", "").strip()
        user = User.get_by_username(username)
    else:
        new_message = msg.reply_text(
            "❌ Вы должны ответить на сообщение пользователя или упомянуть его!"
        )
        auto_delete(new_message, context, from_message=msg)
        return

    if user:
        new_message = update.effective_message.reply_text(
            "Пользователь {} имеет {} рейтинга и {} очков влияния".format(
                user.first_name, f"{user.reputation:.3f}", f"{user.force:.3f}"
            )
        )
    else:
        new_message = update.effective_message.reply_text(
            "Пользователь {} имеет 0.0 рейтинга и 0.0 очков влияния".format(
                user.first_name
            )
        )

    auto_delete(new_message, context, from_message=msg)


def get_logs_data(user_id):
    history = ReputationUpdate.get_history(user_id)

    logs_data = []
    logs_text = ""

    if history:
        for i in range(len(history)):
            from_user = User.get(history[i].from_user_id)
            updated_at = str(history[i].updated_at).split(".")[0]
            updated_at_date = updated_at.split()[0]
            updated_at_time = updated_at.split()[1]

            # round it up so as not to show too large numbers
            history[i].reputation_delta = round(history[i].reputation_delta, 3)
            history[i].force_delta = round(history[i].force_delta, 3)

            rep_delta = (
                "+" + str(history[i].reputation_delta)
                if history[i].reputation_delta > 0
                else str(history[i].reputation_delta)
            )

            force_delta = (
                "+" + str(history[i].force_delta)
                if history[i].force_delta > 0
                else str(history[i].force_delta)
            )

            new_rep = str(round(history[i].new_reputation, 3))

            index = str(i + 1)

            if i % 10 != 0 or i == 0:
                logs_text += f"{index}. <b>{from_user.first_name}</b> изменил(а) репутацию {updated_at_date} в {updated_at_time} ({rep_delta}; {force_delta}). Новая репутация: <i>{new_rep}</i>\n\n"
            else:
                logs_data.append(logs_text)
                logs_text = f"{index}. <b>{from_user.first_name}</b> изменил(а) репутацию {updated_at_date} в {updated_at_time} ({rep_delta}; {force_delta}). Новая репутация: <i>{new_rep}</i>\n\n"

        if logs_text != "":
            logs_data.append(logs_text)

    return logs_data


def reputation_history_callback(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message

    logs_data = get_logs_data(msg.from_user.id)

    if len(logs_data) > 0:
        paginator = InlineKeyboardPaginator(
            len(logs_data), data_pattern="logs#{page}#" + str(msg.from_user.id)
        )

        new_message = msg.reply_html(text=logs_data[0], reply_markup=paginator.markup)

    else:
        new_message = msg.reply_text("❌ У вас ещё нет истории изменения репутации.")

    auto_delete(new_message, context, from_message=msg)


def reputation_history_page_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = int(query.data.split("#")[2])
    query.answer()
    page = int(query.data.split("#")[1])
    if update.callback_query.from_user.id == user_id:
        logs_data = get_logs_data(update.callback_query.from_user.id)

        paginator = InlineKeyboardPaginator(
            len(logs_data),
            current_page=page,
            data_pattern="logs#{page}#" + str(user_id),
        )
        query.edit_message_text(
            text=logs_data[page - 1],
            reply_markup=paginator.markup,
            parse_mode=ParseMode.HTML,
        )
    else:
        query.answer("Вы не можете пользоваться данной клавиатурой")


# on non command i.e message
dispatcher.add_handler(
    MessageHandler(ReputationChangeFilter(), reputation_callback, run_async=True),
    group=1,
)

# show reputation information about a certain person
dispatcher.add_handler(
    CommandHandler("about", about_user_callback, run_async=True), group=7
)

dispatcher.add_handler(
    CommandHandler("history", reputation_history_callback, run_async=True), group=8
)

# called by the keyboard when viewing the reputation history
dispatcher.add_handler(
    CallbackQueryHandler(reputation_history_page_callback, pattern="^logs#")
)

# show reputation rating table
dispatcher.add_handler(
    CommandHandler("rating", show_leaders_callback, run_async=True), group=2
)

# show self rating
dispatcher.add_handler(
    CommandHandler("me", show_self_rating_callback, run_async=True), group=3
)

dispatcher.add_handler(
    CallbackQueryHandler(show_self_rating_position_callback, pattern="^show_pos#")
)
