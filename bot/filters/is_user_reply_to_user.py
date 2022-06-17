from telegram.ext import MessageFilter


class IsUserReplyToUser(MessageFilter):
    name = "is_user_reply_to_user"

    def filter(self, message):
        if message.reply_to_message:
            return True

        return False
