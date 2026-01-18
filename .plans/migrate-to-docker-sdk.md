# Plan: Migrate from Gradio SDK to Docker SDK

## Problem (2026-01-18)

Using Gradio SDK required maintaining both `pyproject.toml` (for local dev with `uv`) and `requirements.txt` (for HF Spaces). This created a maintenance burden and risk of dependency drift.

## Why Migration Is Now Possible

Previously, Docker SDK failed with DNS errors:
```
ClientConnectorDNSError: Cannot connect to host discord.com:443 ssl:default [No address associated with hostname]
```

This was solved by implementing a custom DNS resolver using Google (8.8.8.8) and Cloudflare (1.1.1.1) DNS via aiohttp's `AsyncResolver`. The resolver works at the application level, bypassing HF Spaces' restricted DNS regardless of SDK choice.

## Solution

Switch from Gradio SDK to Docker SDK to use `pyproject.toml` as the single source of truth.

## Implementation

### 1. Update README.md frontmatter

```yaml
---
title: Discord Gemini Bot
emoji: 🤖
colorFrom: yellow
colorTo: purple
sdk: docker
app_file: app.py
python_version: "3.12"
---
```

### 2. Update Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files and README (needed for build)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code and app
COPY src/ ./src/
COPY app.py ./

# Expose Gradio port (HF Spaces expects 7860)
EXPOSE 7860

# Run the Gradio app
CMD ["uv", "run", "python", "app.py"]
```

### 3. Delete requirements.txt

No longer needed.

### 4. Update deploy.yml

Remove `requirements.txt` from paths trigger.

## Files Modified

- `README.md` - Changed `sdk: gradio` → `sdk: docker`, removed `sdk_version`
- `Dockerfile` - Updated to run `app.py`, expose port 7860
- `requirements.txt` - Deleted
- `.github/workflows/deploy.yml` - Removed `requirements.txt` from paths

## Benefits

1. **Single source of truth** - Only `pyproject.toml` for dependencies
2. **Faster installs** - `uv sync` is much faster than pip
3. **No drift risk** - Can't forget to update `requirements.txt`
4. **Consistency** - Same tooling locally and in production
