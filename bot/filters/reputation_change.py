import re
import string
from telegram.ext import MessageFilter
from bot import config


class ReputationChangeFilter(MessageFilter):
    name = 'reputation_filter'
    data_filter = True

    regex_upvote = r"^((?i)\+\+|\+1|\+rep|\+реп|спасибо|спс|спасибочки|благодарю|пасиб|пасиба|пасеба|посеба|благодарочка|thx|мерси|выручил|сяп|сяб|сенк|сенкс|сяпки|сябки|благодарствую|👍)$"
    regex_downvote = r"^(\-\-|\-1|-rep|-реп|👎)$"

    def filter(self, message):
        if message.chat.id == config.MIREA_NINJA_GROUP_ID:
            if message.reply_to_message:
                if message.reply_to_message.from_user.id != message.from_user.id:
                    if message.text:
                        text = message.text.rstrip(
                            string.punctuation).strip().lower()
                        if re.match(self.regex_upvote, text):
                            return {'reputation': [{'reputation_change': 1}]}
                        elif re.match(self.regex_downvote, text):
                            return {'reputation': [{'reputation_change': -1}]}

        return {}
