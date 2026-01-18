"""
Gradio app entry point for HF Spaces.

Launches Discord bot in background thread, serves Gradio status page.
"""

import threading
from datetime import datetime

import gradio as gr

# Bot status tracking
bot_status: dict[str, datetime | bool | str | None] = {
    "started_at": None,
    "is_running": False,
    "last_error": None,
}


def get_status() -> str:
    """Return current bot status as markdown."""
    if not bot_status["is_running"]:
        return "## Bot is starting..."

    started_at = bot_status["started_at"]
    if not isinstance(started_at, datetime):
        return "## Bot is starting..."

    uptime = datetime.now() - started_at
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    status = f"""## Discord Gemini Bot Status

| Metric | Value |
|--------|-------|
| Status | Online |
| Uptime | {hours}h {minutes}m {seconds}s |
| Started | {started_at.strftime("%Y-%m-%d %H:%M:%S UTC")} |
"""

    if bot_status["last_error"]:
        status += f"\n\n**Last Error:** {bot_status['last_error']}"

    return status


def start_discord_bot() -> None:
    """Start the Discord bot in background."""
    import asyncio
    from src.utils.logging import logger

    # Create event loop FIRST - needed for async DNS resolver
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        from src import config
        from src.bot.client import DiscordBot, create_connector_with_custom_dns

        if not config.validate_config():
            bot_status["last_error"] = "Invalid configuration"
            logger.error("Invalid configuration - missing required env vars")
            return

        assert config.DISCORD_TOKEN is not None

        # Log token format (safely - just length and structure)
        token = config.DISCORD_TOKEN
        logger.info(f"Token length: {len(token)}, parts: {len(token.split('.'))}")

        # Create connector with custom DNS to bypass HF Spaces DNS restrictions
        # Must be created AFTER event loop is set
        connector = create_connector_with_custom_dns()
        bot = DiscordBot(connector=connector)

        async def runner(discord_token: str) -> None:
            bot_status["started_at"] = datetime.now()
            bot_status["is_running"] = True
            logger.info("Starting Discord bot connection...")

            try:
                logger.info("Attempting login...")
                await bot.login(discord_token)
                logger.info("Login successful, connecting to gateway...")
                await bot.connect()
            except Exception as e:
                logger.error(f"Discord connection error: {type(e).__name__}: {e}")
                bot_status["last_error"] = f"{type(e).__name__}: {e}"
                bot_status["is_running"] = False
                raise

        try:
            loop.run_until_complete(runner(token))
        except Exception as e:
            logger.error(f"Event loop error: {e}")
        finally:
            loop.close()
    except Exception as e:
        from src.utils.logging import logger
        logger.error(f"Failed to start Discord bot: {e}")
        bot_status["last_error"] = str(e)
        bot_status["is_running"] = False


# Start Discord bot in background thread
bot_thread = threading.Thread(target=start_discord_bot, daemon=True)
bot_thread.start()

# Create Gradio interface
with gr.Blocks(title="Discord Gemini Bot") as demo:
    gr.Markdown("# Discord Gemini Bot")
    gr.Markdown("A multimodal Discord bot powered by Google Gemini 3 and Veo.")

    status_display = gr.Markdown(get_status)
    refresh_btn = gr.Button("Refresh Status")
    refresh_btn.click(fn=get_status, outputs=status_display)


if __name__ == "__main__":
    demo.launch()
