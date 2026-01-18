# Plan: /healthz Endpoint with FastAPI + Gradio Mount

## Problem (2026-01-18)

Need a `/healthz` endpoint for keep-alive pings, but Gradio's routing makes this difficult.

## Previous Attempts

### Attempt 1: `@demo.app.get("/healthz")` (Gradio SDK)

```python
@demo.app.get("/healthz")
def healthz():
    return PlainTextResponse("ok")
```

**Result**: Returns Gradio UI instead of "ok". Gradio's catch-all routing (`/` and `/{page}`) intercepts undefined routes before custom routes are checked.

### Attempt 2: `@demo.app.get("/healthz")` (Docker SDK)

Same approach after migrating to Docker SDK.

**Result**: Returns 404. Better than UI, but route still not registered properly. Gradio rebuilds its internal FastAPI app at launch time, overwriting custom routes.

## Solution: FastAPI as Main App with Gradio Mount

Instead of adding routes to Gradio's internal FastAPI, create our own FastAPI app and mount Gradio on it.

### Implementation

```python
import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

# Create Gradio interface
with gr.Blocks(title="Discord Gemini Bot") as demo:
    # ... Gradio UI components ...

# Create FastAPI app with health endpoint FIRST
app = FastAPI()

@app.get("/healthz")
def healthz() -> PlainTextResponse:
    """Lightweight liveness probe for keep-alive pings."""
    return PlainTextResponse("ok")

# Mount Gradio on FastAPI (Gradio handles "/" and below)
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    # Run with uvicorn instead of demo.launch()
    uvicorn.run(app, host="0.0.0.0", port=7860)
```

### Why This Works

1. **Route priority**: FastAPI routes registered before mounting take precedence
2. **No Gradio interference**: Gradio is mounted as a sub-application at `/`, not as the main app
3. **Clean separation**: Health endpoint lives outside Gradio's routing entirely

### Architecture

```
Request to /healthz
    |
    v
FastAPI app
    |
    +---> /healthz route --> PlainTextResponse("ok")
    |
    +---> /* (everything else) --> Gradio mounted app
```

## Files Modified

- `app.py` - Restructured to use FastAPI + Gradio mount pattern

## Endpoint

- URL: `https://oharu121-discord-gemini-bot.hf.space/healthz`
- Response: `ok` (plain text)
- Use case: Keep-alive pings from Google Apps Script or monitoring services
