import logging
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler


logger = logging.getLogger(__name__)


def setup(dispatcher: Dispatcher):
    logger.info("Setup handlers...")

    from bot.handlers.reputation import reputation_callback, show_leaders_callback, \
        show_self_rating_callback, about_user_callback, reputation_history_callback
    from bot.handlers.rules import rules_callback
    from bot.handlers.users import users_updater
    from bot.handlers.help import help_callback
    from bot.handlers.voice_to_text import voice_to_text_callback
    from bot.filters.reputation_change import ReputationChangeFilter

    # update user data
    dispatcher.add_handler(MessageHandler(
        Filters.all & Filters.chat_type.groups, users_updater, run_async=True))

    # on non command i.e message
    dispatcher.add_handler(MessageHandler(
        ReputationChangeFilter(), reputation_callback, run_async=True), group=1)

    # on non command i.e message
    dispatcher.add_handler(MessageHandler(
        Filters.voice & Filters.chat_type.groups, voice_to_text_callback), group=6)

    # show reputation information about a certain person
    dispatcher.add_handler(CommandHandler(
        'about', about_user_callback, run_async=True), group=7)

    dispatcher.add_handler(CommandHandler(
        'history', reputation_history_callback, run_async=True), group=8)

    # show about information
    dispatcher.add_handler(CommandHandler(
        'help', help_callback), group=4)

    # show reputation rating table
    dispatcher.add_handler(CommandHandler(
        'rating', show_leaders_callback, run_async=True), group=2)

    # show self rating
    dispatcher.add_handler(CommandHandler(
        'me', show_self_rating_callback, run_async=True), group=3)

    # show brief information about the bot
    dispatcher.add_handler(CommandHandler(
        'help', help_callback), group=4)

    # show chat rules
    dispatcher.add_handler(CommandHandler('rules', rules_callback), group=5)
