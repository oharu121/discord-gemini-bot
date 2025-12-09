"""Gradio status page for HF Spaces."""

from datetime import datetime

import gradio as gr

# Track bot status
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
| Started | {started_at.strftime("%Y-%m-%d %H:%M:%S")} |
"""

    if bot_status["last_error"]:
        status += f"\n\n**Last Error:** {bot_status['last_error']}"

    return status


def create_app() -> gr.Blocks:
    """Create Gradio interface."""
    with gr.Blocks(title="Discord Gemini Bot") as app:
        gr.Markdown("# Discord Gemini Bot")
        status_display = gr.Markdown(get_status)
        refresh_btn = gr.Button("Refresh Status")
        refresh_btn.click(fn=get_status, outputs=status_display)

    return app


def launch_gradio() -> None:
    """Launch Gradio server."""
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
