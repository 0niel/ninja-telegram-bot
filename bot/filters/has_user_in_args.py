import re
from telegram.ext import MessageFilter
from bot import config


class HasUserInArgsFilter(MessageFilter):
    name = 'has_user_in_ars_filter'

    def filter(self, message):
        text = message.text.split()

        if len(text) >= 2:
            return re.search(r'@.+', text[1])

        return False
