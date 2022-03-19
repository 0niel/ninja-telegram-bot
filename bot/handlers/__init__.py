import logging
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler


logger = logging.getLogger(__name__)


def setup(dispatcher: Dispatcher):
    logger.info("Setup handlers...")

    from bot.handlers.reputation import reputation_callback, show_leaders_callback, show_self_rating_callback, about_rating_callback
    from bot.handlers.rules import rules_callback
    from bot.handlers.users import users_updater
    from bot.filters.reputation_change import ReputationChangeFilter

    # update user data
    dispatcher.add_handler(MessageHandler(
        Filters.all & Filters.chat_type.groups, users_updater, run_async=True))

    # on non command i.e message
    dispatcher.add_handler(MessageHandler(
        ReputationChangeFilter(), reputation_callback, run_async=True), group=1)

    # show reputation rating table
    dispatcher.add_handler(CommandHandler(
        'rating', show_leaders_callback, run_async=True), group=2)

    # show self rating
    dispatcher.add_handler(CommandHandler(
        'me', show_self_rating_callback, run_async=True), group=3)

    # show about information
    dispatcher.add_handler(CommandHandler(
        'about', about_rating_callback), group=4)

    # show chat rules
    dispatcher.add_handler(CommandHandler('rules', rules_callback), group=5)
