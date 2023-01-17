def setup() -> None:
    """Setup command and message handlers."""

    # Initialize handlers here
    from bot.handlers import help, horoscope, on_any_message, on_join_or_left, reputation, rules, voice_to_text
