# Plan: Fix /healthz Endpoint on HF Spaces

## Problem (2026-01-08)
The `/healthz` endpoint returns Gradio's UI instead of "ok". The original implementation using `@demo.app.get("/healthz")` doesn't work because Gradio's catch-all routing intercepts all undefined routes.

## Root Cause
Gradio's `routes.py` has a catch-all route (`/` and `/{page}`) that serves the HTML interface for any undefined path. Routes added via `@demo.app.get()` are registered AFTER Gradio's router, so the catch-all takes priority.

## Solution
Use `gr.api()` (added in Gradio v5.11, January 2025) to create a proper API endpoint that bypasses Gradio's catch-all routing.

## Implementation

### Update `app.py`

**Remove** the non-working endpoint:
```python
# Add /healthz endpoint to Gradio's underlying FastAPI app
@demo.app.get("/healthz")
def healthz() -> PlainTextResponse:
    """Lightweight liveness probe for keep-alive pings."""
    return PlainTextResponse("ok")
```

**Remove** unused import:
```python
from fastapi.responses import PlainTextResponse
```

**Add** inside the Gradio Blocks context:
```python
with gr.Blocks(title="Discord Gemini Bot") as demo:
    # ... existing UI code ...

    # Add health check API endpoint
    def healthz() -> str:
        return "ok"
    gr.api(healthz, api_name="healthz")
```

### Update Google Apps Script
Change the ping URL:
- Old: `https://oharu121-discord-gemini-bot.hf.space/healthz`
- New: `https://oharu121-discord-gemini-bot.hf.space/gradio_api/call/healthz`

## Files Modified
- `app.py`

## Why This Works
- `gr.api()` is Gradio's official way to add custom API endpoints
- Endpoint is accessible at `/gradio_api/call/healthz`
- No changes to Gradio SDK architecture - Discord connection unaffected
- Keeps the working Gradio SDK setup intact
