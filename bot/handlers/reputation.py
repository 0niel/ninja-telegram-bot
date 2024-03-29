import logging

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler
from telegram_bot_pagination import InlineKeyboardPaginator

from bot import application
from bot.filters import IsChatAllowedFilter
from bot.filters.has_user_in_args import HasUserInArgsFilter
from bot.filters.reputation_change import ReputationChangeFilter
from bot.handlers.on_any_message import users_updater
from bot.models.reputation_update import ReputationUpdate
from bot.services import reputation_update
from bot.services import user as user_service
from bot.services.reputation import compute_force
from bot.services.reputation import compute_rep
from bot.services.reputation import get_rating_by_slice

logger = logging.getLogger(__name__)


async def on_reputation_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.reputation:
        return

    error_message = None

    message = update.effective_message

    if not message.reply_to_message:
        return
    elif message.from_user.is_bot:
        error_message = await message.reply_text("❌ Изменять репутацию может только пользователь!")
    elif message.reply_to_message.from_user.id == message.from_user.id:
        error_message = await message.reply_text("❌ Вы не можете изменить репутацию самому себе!")
    elif message.reply_to_message.from_user.is_bot:
        error_message = await message.reply_text("❌ Вы не можете изменить репутацию бота!")

    if error_message:
        return

    from_user_id = message.from_user.id
    to_user_id = message.reply_to_message.from_user.id

    from_user = await user_service.get_by_id(from_user_id)
    to_user = await user_service.get_by_id(to_user_id)

    if from_user is None or to_user is None:
        # Call updater directly
        await users_updater(update, context)

        from_user = await user_service.get_by_id(from_user_id)
        to_user = await user_service.get_by_id(to_user_id)

    if (
        from_user.update_reputation_at and user_service.is_rep_change_available(from_user, 10 * 60) is False
    ):  # 10 minutes
        await message.reply_text("❌ Репутацию можно изменять один раз в 10 минут!")
        return

    if await reputation_update.is_user_send_rep_to_message(from_user_id, message.reply_to_message.message_id):
        await message.reply_text("❌ Вы уже изменяли репутацию, используя это сообщение!")
        return

    reputation_change = context.reputation[0]["reputation_change"]

    new_user_rep_delta = round(compute_rep(reputation_change, from_user.force), 5)
    new_user_force_delta = round(compute_force(reputation_change, from_user.force), 5)

    new_user_force = round(to_user.force + new_user_force_delta, 3)
    new_user_rep = round(to_user.reputation + new_user_rep_delta, 3)

    await user_service.update_rep_and_force(from_user_id, to_user_id, new_user_rep, new_user_force)

    await reputation_update.create(
        ReputationUpdate(
            message_id=message.reply_to_message.message_id,
            from_tg_user_id=from_user_id,
            to_tg_user_id=to_user_id,
            reputation_delta=new_user_rep_delta,
            force_delta=new_user_force_delta,
            new_reputation=new_user_rep,
            new_force=new_user_force,
        )
    )

    from_username = message.from_user.first_name
    to_username = message.reply_to_message.from_user.first_name

    new_user_rep_delta = round(new_user_rep_delta, 3)

    new_rep = f"+{str(new_user_rep_delta)}" if new_user_rep_delta > 0 else str(new_user_rep_delta)

    icon = "👎" if reputation_change < 0 else "👍"

    logger.info(f"{from_username} has updated {to_username} reputation {new_rep}")

    await context.bot.send_message(
        message.chat_id,
        (
            f"{icon} *{from_username}* ({from_user.reputation:.3f}, {from_user.force:.3f}) "
            f"обновил(а) вам репутацию ({new_rep})"
        ),
        reply_to_message_id=message.reply_to_message.message_id,
        parse_mode=ParseMode.MARKDOWN,
    )


async def show_leaders(update: Update, context: CallbackContext):
    leaders = await user_service.get_top_by_reputation(15)

    if not leaders:
        await update.effective_message.reply_text("На данный момент нет активных участников для формирования рейтинга")
        return

    rating_message = "📊 <b>Рейтинг пользователей:</b>\n\n"

    lines = []
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    for i in range(len(leaders)):
        medal = ""
        if i in medals:
            medal = medals[i]
        reputation = f"{leaders[i].reputation:.3f}"
        force = f"{leaders[i].force:.3f}"
        lines.append(
            f'{str(i + 1)}. {f"{leaders[i].first_name} " + (leaders[i].last_name if leaders[i].last_name is not None else "")} - {reputation if leaders[i].reputation >= 0 else f"({reputation})"} репутации и {force} влияния {medal}'
        )

    return await update.effective_message.reply_html(rating_message + "\n".join(lines))


async def show_self_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_message.from_user.id
    user = await user_service.get_by_id(user_id)

    keyboard = [
        [InlineKeyboardButton("📈 Показать позицию в рейтинге", callback_data=f"show_pos#{str(user_id)}")],
    ]

    await update.effective_message.reply_html(
        text=(
            f'{update.effective_message.from_user.first_name}, у вас <b>{user.reputation:.3f}</b> '
            f'репутации и <b>{user.force:.3f}</b> очков влияния'
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )




async def show_self_rating_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.data.split("#")[1])
    if update.callback_query.from_user.id == user_id:
        if rating_slice := await user_service.get_rating_slice(user_id, 5, 5):  # type: list[tuple["User", int]]
            text = get_rating_by_slice(rating_slice, user_id)
            await query.edit_message_text(text=text, parse_mode=ParseMode.MARKDOWN)
            await query.answer()
        else:
            await query.answer("Для вас ещё не сформировалась позиция в рейтинге")
    else:
        await query.answer("Вы не можете пользоваться данной клавиатурой")


async def about_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if msg.reply_to_message:
        from_user_id = msg.reply_to_message.from_user.id
        user = await user_service.get_by_id(from_user_id)
    elif HasUserInArgsFilter().filter(msg):
        username = context.args[0].replace("@", "").strip()
        user = await user_service.get_by_username(username)
    else:
        await msg.reply_text("❌ Вы должны ответить на сообщение пользователя или упомянуть его!")
        return

    if user:
        await update.effective_message.reply_html(
            text=(
                f'Пользователь <b>{user.first_name}</b> имеет <b>{user.reputation:.3f}</b> '
                f'репутации и <b>{user.force:.3f}</b> очков влияния'
            )
        )
    else:
        await update.effective_message.reply_html(
            text=(
                f"Пользователь <b>{user.first_name}</b> имеет <b>0.0</b> репутации и <b>0.0</b> очков влияния"
            )
        )





async def get_logs_data(user_id: int):
    history = await reputation_update.get_by_user_id(user_id)

    logs_data = []
    logs_text = ""

    if history:
        for i, log in enumerate(history):
            from_user = await user_service.get_by_id(log.from_tg_user_id)
            updated_at = str(log.updated_at).split(".")[0]
            updated_at_date, updated_at_time = updated_at.split()

            log.reputation_delta = round(log.reputation_delta, 3)
            log.force_delta = round(log.force_delta, 3)

            rep_delta = f"+{log.reputation_delta}" if log.reputation_delta > 0 else str(log.reputation_delta)
            force_delta = f"+{log.force_delta}" if log.force_delta > 0 else str(log.force_delta)
            new_rep = str(round(log.new_reputation, 3))

            index = str(i + 1)

            entry_text = (
                f"{index}. <b>{from_user.first_name}</b> изменил(а) репутацию {updated_at_date} "
                f"в {updated_at_time} ({rep_delta}; {force_delta}). Новая репутация: <i>{new_rep}</i>\n\n"
            )

            if i % 10 != 0 or i == 0:
                logs_text += entry_text
            else:
                logs_data.append(logs_text)
                logs_text = entry_text

        if logs_text != "":
            logs_data.append(logs_text)

    return logs_data


async def reputation_change_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    logs_data = await get_logs_data(msg.from_user.id)

    if len(logs_data) > 0:
        paginator = InlineKeyboardPaginator(len(logs_data), data_pattern="logs#{page}#" + str(msg.from_user.id))
        await msg.reply_html(text=logs_data[0], reply_markup=paginator.markup)

    else:
        await msg.reply_text("❌ У вас ещё нет истории изменения репутации.")


async def reputation_history_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.data.split("#")[2])

    if update.callback_query.from_user.id == user_id:
        logs_data = await get_logs_data(update.callback_query.from_user.id)

        page = int(query.data.split("#")[1])
        paginator = InlineKeyboardPaginator(
            len(logs_data),
            current_page=page,
            data_pattern="logs#{page}#" + str(user_id),
        )
        await query.edit_message_text(
            text=logs_data[page - 1],
            reply_markup=paginator.markup,
            parse_mode=ParseMode.HTML,
        )
        await query.answer()
    else:
        await query.answer("Вы не можете пользоваться данной клавиатурой")


# show reputation information about a certain person
application.add_handler(CommandHandler("about", about_user_callback))

application.add_handler(CommandHandler("history", reputation_change_history))

# called by the keyboard when viewing the reputation history
application.add_handler(CallbackQueryHandler(reputation_history_page_callback, pattern="^logs#"))

# show reputation rating table
application.add_handler(CommandHandler("rating", show_leaders))

# show self rating
application.add_handler(CommandHandler("me", show_self_rating))

application.add_handler(CallbackQueryHandler(show_self_rating_position, pattern="^show_pos#"))

# on non command i.e message
application.add_handler(MessageHandler(ReputationChangeFilter() & IsChatAllowedFilter(), on_reputation_change))
