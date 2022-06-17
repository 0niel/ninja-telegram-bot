import builtins
import io
import json
import os
import re
from pathlib import Path

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode,
                      Update)
from telegram.ext import CallbackContext
from telegram.utils.helpers import escape_markdown
from telegram_bot_pagination import InlineKeyboardPaginator

from bot import config
from bot.models.user import User
from bot.models.user_script import UserScript
from bot.utils.safe_exec.executor import Executor

RE_SCRIPT_NAME = r"^[a-zA-Z0-9_-]{1,30}$"


def safe_exec(exec_command, update: Update, context: CallbackContext):
    try:
        safe_locals_names = [
            "update",
            # "context", ? must be unsafe
        ]

        safe_locals = {}
        for item in safe_locals_names:
            safe_locals[item] = locals().get(item, None)

        safe_builtins = globals()["__builtins__"]
        safe_builtins["print"] = update.message.reply_text
        safe_builtins["BytesIO"] = io.BytesIO

        Executor().execute(
            exec_command,
            {"__builtins__": safe_builtins},
            safe_locals,
        )

    except Exception as msg:
        msg = str(msg)
        msg = msg.replace(
            "'NoneType' object is not subscriptable", "Операция запрещена!"
        )
        update.message.reply_text(text=str(msg))


def save_script_handler(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id != config.MIREA_NINJA_GROUP_ID:
        return

    script_text = update.message.text.replace("/save", "").strip()
    script_name = script_text.split()[0].strip()
    script_description = script_text.split("\n")[1].strip()
    script_text = "\n".join(script_text.split("\n")[2:])

    if re.match(RE_SCRIPT_NAME, script_name) is None:
        update.message.reply_text("❌ Нельзя создать скрипт с таким названием!")
        return
    if len(script_name) < 2 or len(script_name) > 40:
        update.message.reply_text(
            "❌ Название скрипта должно быть не короче 2-х сиволов и не длиннее 40"
        )
        return
    if UserScript.get_by_name(script_name):
        update.message.reply_text(
            "❌ Пользовательский скрипт с таким названием уже существует!"
        )
        return
    if len(script_text) > 2000:
        update.message.reply_text(
            "❌ Количество символов в скрипте не должно привышать 2000!"
        )
        return
    elif len(script_text) < 2:
        update.message.reply_text("❌ Вы пытаетесь сохранить пустой скрипт")
        return
    if len(script_description) < 2 or len(script_description) > 300:
        update.message.reply_text(
            "❌ Описание скрипта не должно быть пустым и должно быть не длиннее 300 символов"
        )
        return

    from_user_id = update.message.from_user.id
    author = User.get(from_user_id)
    UserScript.create(author.id, script_name, script_text, script_description)
    update.message.reply_text(
        f"✅ Скрипт сохранён с названием {script_name}. Используйте /load {script_name}, чтобы запустить его"
    )


def load_script_handler(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id != config.MIREA_NINJA_GROUP_ID:
        return

    command_args = context.args
    script_name = command_args[0]
    user_script = UserScript.get_by_name(script_name)
    if not user_script:
        update.message.reply_text(
            "❌ Пользовательского скрипта с таким названием не существует!"
        )
        return

    args = command_args[1:]
    args = f"args = {json.dumps(args)}\n" if len(args) > 0 else ""
    safe_exec(args + user_script.script, update, context)


def exec_handler(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id != config.MIREA_NINJA_GROUP_ID:
        return

    exec_command = update.message.text.replace("/exec", "").strip()
    safe_exec(exec_command, update, context)


def script_rename_handler(update: Update, context: CallbackContext) -> None:
    command_args = context.args
    old_script_name = command_args[0]
    new_script_name = command_args[1]
    user = User.get(update.message.from_user.id)
    user_script = UserScript.get_by_name(old_script_name)

    if not user_script:
        update.message.reply_text(
            "❌ Пользовательского скрипта с таким названием не существует!"
        )
        return
    if user_script.author_id != user.id:
        update.message.reply_text("❌ Переименовать скрипт может только его автор!")
        return
    if re.match(RE_SCRIPT_NAME, new_script_name) is None:
        update.message.reply_text("❌ Нельзя переименовать скрипт в это название!")
        return

    UserScript.rename(old_script_name, new_script_name)
    update.message.reply_text(
        f"✅ Скрипт {old_script_name} успешно переименован в {new_script_name}"
    )


def script_delete_handler(update: Update, context: CallbackContext) -> None:
    command_args = context.args
    script_name = command_args[0]
    user = User.get(update.message.from_user.id)
    user_script = UserScript.get_by_name(script_name)

    if not user_script:
        update.message.reply_text(
            "❌ Пользовательского скрипта с таким названием не существует!"
        )
        return
    if user_script.author_id != user.id:
        update.message.reply_text("❌ Удалить скрипт может только его автор!")
        return

    UserScript.delete_by_name(script_name)
    update.message.reply_text(f"✅ Скрипт {script_name} успешно удалён")


def script_changedesc_handler(update: Update, context: CallbackContext) -> None:
    args = update.message.text.replace("/changedesc", "").strip()
    script_name = args.split()[0].strip()
    new_script_description = args.split("\n")[1].strip()
    user = User.get(update.message.from_user.id)
    user_script = UserScript.get_by_name(script_name)

    if not user_script:
        update.message.reply_text(
            "❌ Пользовательского скрипта с таким названием не существует!"
        )
        return
    if user_script.author_id != user.id:
        update.message.reply_text("❌ Изменить описание скрипта может только его автор!")
        return
    if len(new_script_description) < 2 or len(new_script_description) > 300:
        update.message.reply_text(
            "❌ Описание скрипта не должно быть пустым и должно быть не длиннее 300 символов"
        )
        return

    UserScript.change_desc(script_name, new_script_description)
    update.message.reply_text(f"✅ Описание скрипта {script_name} успешно обновлено")


def get_scripts_data():
    scripts = UserScript.get_all()

    scripts_data = []
    scripts_text = ""

    if scripts:
        for i in range(len(scripts)):
            author = User.get(scripts[i].author_id)

            index = str(i + 1)

            if i % 10 != 0 or i == 0:
                scripts_text += f"{index}\. *{scripts[i].name}* \- {escape_markdown(scripts[i].description, version=2)}\. Автор скрипта \- {author.first_name}\n\n"
            else:
                scripts_data.append(scripts_text)
                scripts_text = f"{index}\. *{scripts[i].name}* \- {escape_markdown(scripts[i].description, version=2)}\. Автор скрипта \- {author.first_name}\n\n"

        if scripts_text != "":
            scripts_data.append(scripts_text)

    return scripts_data


def scripts_handler(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id != config.MIREA_NINJA_GROUP_ID:
        return

    msg = update.effective_message

    logs_data = get_scripts_data()

    if len(logs_data) > 0:
        paginator = InlineKeyboardPaginator(
            len(logs_data), data_pattern="scripts#{page}#" + str(msg.from_user.id)
        )

        new_message = msg.reply_text(
            text=logs_data[0],
            reply_markup=paginator.markup,
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    else:
        new_message = msg.reply_text("❌ Сейчас нет ни одного скрипта.")


def scripts_callback_page_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = int(query.data.split("#")[2])
    query.answer()
    page = int(query.data.split("#")[1])
    if update.callback_query.from_user.id == user_id:
        logs_data = get_scripts_data()

        paginator = InlineKeyboardPaginator(
            len(logs_data),
            current_page=page,
            data_pattern="scripts#{page}#" + str(user_id),
        )
        query.edit_message_text(
            text=logs_data[page - 1],
            reply_markup=paginator.markup,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    else:
        query.answer("Вы не можете пользоваться данной клавиатурой")
