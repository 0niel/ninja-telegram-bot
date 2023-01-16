import re

from telegram.ext.filters import MessageFilter


class HasUserInArgsFilter(MessageFilter):
    name = "has_user_in_ars_filter"

    def filter(self, message):
        text = message.text.split()

        return re.search(r"@.+", text[1]) if len(text) >= 2 else False
