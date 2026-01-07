# Plan: Gradio Status Page + /healthz Endpoint on Single Port

## Goal
- Gradio web UI at `/` showing bot status
- `/healthz` endpoint returning "ok" for keep-alive pings
- Both on port 7860 (HF Spaces default)

## Approach (Updated 2026-01-07)
Use **threading** to run Gradio in a daemon thread while Discord bot runs in the main thread. This provides complete isolation between the web server and bot event loops.

**Why not asyncio?** Running both Uvicorn and Discord bot on the same asyncio event loop causes connection failures due to event loop conflicts. The threading approach was the original working implementation.

## Implementation

### 1. `src/app.py` - Gradio module with /healthz

```python
from datetime import datetime
from fastapi.responses import PlainTextResponse
import gradio as gr

bot_status: dict[str, datetime | bool | str | None] = {
    "started_at": None,
    "is_running": False,
    "last_error": None,
}

def get_status() -> str:
    # Return bot status as markdown table

def create_app() -> gr.Blocks:
    # Create Gradio interface with status display and refresh button

def launch_gradio() -> None:
    app = create_app()

    # Add /healthz to Gradio's underlying FastAPI app
    @app.app.get("/healthz")
    def healthz() -> PlainTextResponse:
        return PlainTextResponse("ok")

    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
```

### 2. `src/main.py` - Threading approach

```python
import os
import threading
from datetime import datetime

def main() -> None:
    if not config.validate_config():
        return

    # Start Gradio in daemon thread (only on HF Spaces)
    if os.getenv("SPACE_ID"):
        from src.app import bot_status, launch_gradio

        gradio_thread = threading.Thread(target=launch_gradio, daemon=True)
        gradio_thread.start()

        bot_status["started_at"] = datetime.now()
        bot_status["is_running"] = True

    bot = DiscordBot()
    bot.run(config.DISCORD_TOKEN)  # Blocking - runs in main thread
```

## Files Modified
- [src/main.py](src/main.py) - Threading approach
- [src/app.py](src/app.py) - Gradio module with /healthz endpoint
- [pyproject.toml](pyproject.toml) - Removed uvicorn/fastapi (Gradio handles its own server)

## Why This Works
- **Thread isolation**: Gradio runs in daemon thread, Discord bot runs in main thread
- **Separate event loops**: Each thread has its own event loop, no conflicts
- **HF Spaces only**: Gradio only launches when `SPACE_ID` env var is set (auto-set by HF)
- **Clean shutdown**: Daemon thread auto-terminates when main thread exits

## Result
- `GET /` → Gradio status page (uptime, started time, errors)
- `GET /healthz` → "ok" for keep-alive pings
- Both on port 7860
