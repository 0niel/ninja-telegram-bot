from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from bot.services.auto_delete import auto_delete


def help_callback(update: Update, context: CallbackContext) -> None:
    new_message = update.effective_message.reply_text(
        "- Система репутации:\n"
        "*Репутация* - это основной показатель вашего рейтинга. Чем выше репутация, тем больше вклада вы внесли в общение в беседе Mirea Ninja.\n\n"
        "*Влияние* - это показатель того, насколько ваш голос силен. Сила набирается вслед за репутацией, но не снижается вместе с ней.\n\n имеет доступ к следующим модулям: telegram, requests, PIL, math, re, random.\n\n"
        "/scripts - посмотреть список доступных скриптов\n\n"
        "/load <script\_name> <script\_args>- загрузить скрипт\n\n"
        "/save <script\_name>\n"
        "_следующая строка:_ <script\_description>\n"
        "_следующая строка и остальные:_ <script>\n"
        "- создать новый скрипт\n\n"
        "/rename <old\_script\_name> <new\_script\_name> - переименовать скрипт\n\n"
        "/changedesc <script\_name>\n"
        "_следующая строка:_ <new\_script\_desc> \n"
        "- изменить описание скрипта\n\n"
        "/delete <script\_name> - удалить скрипт",
        parse_mode=ParseMode.MARKDOWN,
    )

    auto_delete(new_message, context, from_message=update.effective_message)
