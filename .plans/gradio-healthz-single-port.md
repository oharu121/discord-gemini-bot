# Plan: Gradio Status Page + /healthz Endpoint on Single Port

## Goal
- Gradio web UI at `/` showing bot status
- `/healthz` endpoint returning "ok" for keep-alive pings
- Both on port 7860 (HF Spaces default)

## Approach
Mount Gradio on a FastAPI app that also has the `/healthz` endpoint. Gradio is built on FastAPI, so this is the standard pattern.

## Implementation

### 1. Modify `src/main.py`

```python
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import gradio as gr
import uvicorn

# FastAPI app with health endpoint
fastapi_app = FastAPI()

@fastapi_app.get("/healthz")
async def healthz() -> PlainTextResponse:
    return PlainTextResponse("ok")

def create_gradio_app() -> gr.Blocks:
    # ... existing Gradio code ...

async def main_async() -> None:
    # Create Gradio app and mount on FastAPI
    gradio_app = create_gradio_app()
    gr.mount_gradio_app(fastapi_app, gradio_app, path="/")

    # Launch server
    config_server = uvicorn.Config(fastapi_app, host="0.0.0.0", port=7860)
    server = uvicorn.Server(config_server)
    asyncio.create_task(server.serve())

    # Start Discord bot
    _bot = DiscordBot()
    await _bot.start(config.DISCORD_TOKEN)
```

### 2. Add dependencies to `pyproject.toml`
- `fastapi`
- `uvicorn`

### 3. Update `CHANGELOG.md`
Add `/healthz` endpoint entry.

## Files to Modify
- [src/main.py](src/main.py) - Mount Gradio on FastAPI with /healthz
- [pyproject.toml](pyproject.toml) - Add fastapi, uvicorn dependencies
- [CHANGELOG.md](CHANGELOG.md) - Document changes

## Result
- `GET /` → Gradio status page
- `GET /healthz` → "ok"
- Both on port 7860
