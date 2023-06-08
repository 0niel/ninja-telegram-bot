def setup() -> None:
    """Setup command and message handlers."""

    # Initialize handlers here
    from bot.handlers import help
    from bot.handlers import horoscope
    from bot.handlers import on_any_message
    from bot.handlers import on_join_or_left
    from bot.handlers import reputation
    from bot.handlers import rules
    from bot.handlers import trust_levels
    from bot.handlers import voice_to_text
