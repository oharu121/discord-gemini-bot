"""Entry point for Discord Gemini Bot."""

import asyncio
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import gradio as gr
import uvicorn

from src import config
from src.bot.client import DiscordBot

# Global reference to bot for status endpoint
_bot: DiscordBot | None = None
_start_time: datetime | None = None

# FastAPI app for health endpoint
fastapi_app = FastAPI()


@fastapi_app.get("/healthz")
async def healthz() -> PlainTextResponse:
    """Lightweight liveness probe for keep-alive pings."""
    return PlainTextResponse("ok")


def get_status() -> str:
    """Get bot status information."""
    if _bot is None or not _bot.is_ready():
        return "Bot is starting..."

    uptime = ""
    if _start_time:
        delta = datetime.now(timezone.utc) - _start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{hours}h {minutes}m {seconds}s"

    guilds = len(_bot.guilds)
    user = _bot.user

    return f"""**Status:** Online
**User:** {user}
**Guilds:** {guilds}
**Uptime:** {uptime}"""


def create_gradio_app() -> gr.Blocks:
    """Create the Gradio status interface."""
    with gr.Blocks(title="Discord Gemini Bot") as app:
        gr.Markdown("# Discord Gemini Bot")
        status_display = gr.Markdown(get_status)
        refresh_btn = gr.Button("Refresh Status")
        refresh_btn.click(fn=get_status, outputs=status_display)

    return app


async def main_async() -> None:
    """Start the Gradio app and Discord bot."""
    global _bot, _start_time

    assert config.DISCORD_TOKEN is not None

    # Create Gradio app and mount on FastAPI
    gradio_app = create_gradio_app()
    gr.mount_gradio_app(fastapi_app, gradio_app, path="/")

    # Launch FastAPI server with Gradio mounted
    server_config = uvicorn.Config(
        fastapi_app, host="0.0.0.0", port=7860, log_level="info"
    )
    server = uvicorn.Server(server_config)
    asyncio.create_task(server.serve())

    # Start Discord bot
    _bot = DiscordBot()
    _start_time = datetime.now(timezone.utc)
    await _bot.start(config.DISCORD_TOKEN)


def main() -> None:
    """Start the Discord bot and Gradio app."""
    if not config.validate_config():
        return

    asyncio.run(main_async())


if __name__ == "__main__":
    main()
