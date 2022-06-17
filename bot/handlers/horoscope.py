import logging

import requests
from bs4 import BeautifulSoup
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode,
                      Update)
from telegram.ext import CallbackContext
from telegram.utils.helpers import escape_markdown
from telegram_bot_pagination import InlineKeyboardPaginator

from bot.models.user import User
from bot.services.auto_delete import auto_delete
from bot.services.reputation import (compute_force, compute_rep, get_rating,
                                     get_rating_by_slice)

logger = logging.getLogger(__name__)


signs = [
    {"aries": "♈ Овен"},
    {"taurus": "♉ Телец"},
    {"gemini": "♊ Близнецы"},
    {"cancer": "♋ Рак"},
    {"leo": "♌ Лев"},
    {"virgo": "♍ Дева"},
    {"libra": "♎ Весы"},
    {"scorpio": "♏ Скорпион"},
    {"sagittarius": "♐ Стрелец"},
    {"capricorn": "♑ Козерог"},
    {"aquarius": "♒ Водолей"},
    {"pisces": "♓ Рыбы"},
]

dates = [
    {"today": "сегодня"},
    {"tomorrow": "завтра"},
    {"week": "неделю"},
    {"month": "месяц"},
]


def show_horoscope_signs_callback(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_message.from_user.id

    i = 0
    keyboard_lines = []
    keyboard = []
    for horo_sign in signs:
        for key, value in horo_sign.items():
            keyboard_lines.append(
                InlineKeyboardButton(
                    value, callback_data=f"show_horo_time#{key}#{str(user_id)}"
                )
            )
            i += 1

            if i == 4:
                i = 0
                keyboard.append(keyboard_lines)
                keyboard_lines = []

    new_message = update.effective_message.reply_text(
        "Самые точные прогнозы на ближайшее будущее специально для участников беседы Mirea Ninja!",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    auto_delete(new_message, context, from_message=update.effective_message, seconds=95)


def show_horo_time_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = int(query.data.split("#")[2])
    sign = query.data.split("#")[1]
    if update.callback_query.from_user.id == user_id:
        keyboard_lines = []
        keyboard = []
        i = 0
        for date_tmp in dates:
            for key, value in date_tmp.items():
                keyboard_lines.append(
                    InlineKeyboardButton(
                        value, callback_data=f"show_horo#{key}#{str(user_id)}#{sign}"
                    )
                )
                i += 1

            if i == 2:
                i = 0
                keyboard.append(keyboard_lines)
                keyboard_lines = []

        for sign_tmp in signs:
            if sign in sign_tmp:
                sign = sign_tmp[sign]

        query.edit_message_text(
            text=f"Выберите, на какую дату показывать прогноз для {sign}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        query.answer()
    else:
        query.answer("Вы не можете пользоваться данной клавиатурой")


def show_horo_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = int(query.data.split("#")[2])
    time = query.data.split("#")[1]
    sign = query.data.split("#")[3]
    if update.callback_query.from_user.id == user_id:
        horo_url = f"https://horo.mail.ru/prediction/{sign}/{time}/"
        html = requests.get(horo_url).text
        bs4 = BeautifulSoup(html, "html.parser")
        text = bs4.select_one(
            "body > div.layout > div:nth-child(3) > div > div.block.block_collapse.block_parallax.block_inner_shadow.block_no_overflow.block_black > div.wrapper.wrapper_outside.wrapper_6857 > div > div > div > div.cols__column.cols__column_small_32.cols__column_medium_43.cols__column_large_47 > div > div > div.p-prediction__inner > div.article.article_white.article_prediction.article_collapsed.margin_top_20 > div > div"
        ).text.replace("\n", "\n\n")

        keyboard = [
            [
                InlineKeyboardButton(
                    "<- Назад", callback_data=f"show_horo_time#{sign}#{str(user_id)}"
                )
            ],
        ]

        query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
        query.answer()
    else:
        query.answer("Вы не можете пользоваться данной клавиатурой")
