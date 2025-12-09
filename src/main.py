"""Entry point for Discord Gemini Bot."""

from src import config
from src.bot.client import DiscordBot


def main() -> None:
    """Start the Discord bot."""
    if not config.validate_config():
        return

    # Token is validated above, assert for type checker
    assert config.DISCORD_TOKEN is not None

    bot = DiscordBot()
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
