"""Entry point for Discord Gemini Bot."""

import os
import threading
from datetime import datetime

from src import config
from src.bot.client import DiscordBot


def main() -> None:
    """Start the Discord bot with Gradio status page on HF Spaces."""
    if not config.validate_config():
        return

    # Start Gradio on HF Spaces (SPACE_ID is auto-set by HF)
    if os.getenv("SPACE_ID"):
        from src.app import bot_status, launch_gradio

        gradio_thread = threading.Thread(target=launch_gradio, daemon=True)
        gradio_thread.start()

        bot_status["started_at"] = datetime.now()
        bot_status["is_running"] = True

    # Token is validated above, assert for type checker
    assert config.DISCORD_TOKEN is not None

    bot = DiscordBot()
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
