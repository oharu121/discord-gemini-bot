"""
Gradio app entry point for HF Spaces.

Launches Discord bot in background thread, serves Gradio status page.
"""

import threading
from datetime import datetime

import gradio as gr
from fastapi.responses import PlainTextResponse

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
    try:
        from src import config
        from src.bot.client import DiscordBot

        if not config.validate_config():
            bot_status["last_error"] = "Invalid configuration"
            return

        bot_status["started_at"] = datetime.now()
        bot_status["is_running"] = True

        assert config.DISCORD_TOKEN is not None
        bot = DiscordBot()
        bot.run(config.DISCORD_TOKEN)
    except Exception as e:
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


# Add /healthz endpoint to Gradio's underlying FastAPI app
@demo.app.get("/healthz")
def healthz() -> PlainTextResponse:
    """Lightweight liveness probe for keep-alive pings."""
    return PlainTextResponse("ok")


if __name__ == "__main__":
    demo.launch()
