import re
import string

from telegram.ext.filters import MessageFilter


class ReputationChangeFilter(MessageFilter):
    name = "reputation_filter"
    data_filter = True

    regex_upvote = (
        r"^(\+\+|\+1|\+rep|\+реп|спасибо|спс|спасибочки|благодарю|пасиб|пасиба|пасеба|посеба|благодарочка"
        r"|thx|мерси|выручил|сяп|сяб|сенк|сенкс|сяпки|сябки|благодарствую|👍)$"
    )
    regex_downvote = r"^(\-\-|\-1|-rep|-реп|👎)$"

    def filter(self, message):
        if message.text:
            text = message.text.rstrip(string.punctuation).strip().lower()
            if re.match(self.regex_upvote, text):
                return {"reputation": [{"reputation_change": 1}]}
            elif re.match(self.regex_downvote, text):
                return {"reputation": [{"reputation_change": -1}]}

        return
