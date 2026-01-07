# Plan: Gradio Status Page + /healthz Endpoint on Single Port

## Goal
- Gradio web UI at `/` showing bot status
- `/healthz` endpoint returning "ok" for keep-alive pings
- Both on port 7860 (HF Spaces default)

## Approach (Updated 2026-01-07)
Use **Gradio SDK** (not Docker) with the Discord bot running in a background thread.

**Why Gradio SDK?** Docker SDK on HF Spaces has DNS issues that prevent connecting to discord.com. Gradio SDK avoids these networking restrictions.

## Implementation

### Architecture
```
HF Spaces (Gradio SDK)
    |
    +---> app.py (root level) - Entry point
              |
              +---> Gradio interface (main thread)
              |         - Status page at /
              |         - /healthz endpoint
              |
              +---> Discord bot (background daemon thread)
                        - Connects to Discord gateway
                        - Runs bot.run() blocking call
```

### Key Files

#### `app.py` (root level - HF Spaces entry point)
```python
import threading
from datetime import datetime
import gradio as gr
from fastapi.responses import PlainTextResponse

bot_status = {"started_at": None, "is_running": False, "last_error": None}

def start_discord_bot() -> None:
    """Start Discord bot in background thread."""
    from src import config
    from src.bot.client import DiscordBot

    bot_status["started_at"] = datetime.now()
    bot_status["is_running"] = True

    bot = DiscordBot()
    bot.run(config.DISCORD_TOKEN)

# Start bot in background thread
bot_thread = threading.Thread(target=start_discord_bot, daemon=True)
bot_thread.start()

# Create Gradio interface
with gr.Blocks(title="Discord Gemini Bot") as demo:
    gr.Markdown("# Discord Gemini Bot")
    status_display = gr.Markdown(get_status)
    refresh_btn = gr.Button("Refresh Status")
    refresh_btn.click(fn=get_status, outputs=status_display)

# Add /healthz endpoint
@demo.app.get("/healthz")
def healthz():
    return PlainTextResponse("ok")

if __name__ == "__main__":
    demo.launch()
```

#### `README.md` metadata
```yaml
---
title: Discord Gemini Bot
emoji: 🤖
colorFrom: yellow
colorTo: purple
sdk: gradio
sdk_version: 5.33.0
app_file: app.py
python_version: "3.12"
---
```

#### `requirements.txt` (for HF Spaces)
```
discord.py>=2.6.4
google-genai>=1.52.0
gradio>=5.33.0
pillow>=12.0.0
python-dotenv>=1.2.1
aiohttp>=3.9.0
```

### Local Development
`src/main.py` remains for local development with `uv run start`.

## Why This Works
- **Gradio SDK**: No Docker networking/DNS issues
- **Thread isolation**: Bot runs in daemon thread, Gradio in main thread
- **Separate event loops**: Each thread manages its own event loop
- **Clean shutdown**: Daemon thread auto-terminates when main thread exits

## Result
- `GET /` → Gradio status page (uptime, started time, errors)
- `GET /healthz` → "ok" for keep-alive pings
- Both on port 7860
