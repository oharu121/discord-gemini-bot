"""Entry point for Discord Gemini Bot."""

import os
import socket
import threading
from datetime import datetime

from src import config
from src.bot.client import DiscordBot


def check_dns() -> None:
    """Check DNS resolution for debugging."""
    hosts = ["discord.com", "generativelanguage.googleapis.com", "google.com"]
    for host in hosts:
        try:
            ip = socket.gethostbyname(host)
            print(f"DNS OK: {host} -> {ip}")
        except socket.gaierror as e:
            print(f"DNS FAIL: {host} -> {e}")


def main() -> None:
    """Start the Discord bot with Gradio status page on HF Spaces."""
    # Debug DNS on HF Spaces
    if os.getenv("SPACE_ID"):
        check_dns()

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
