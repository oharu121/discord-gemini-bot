---
title: Discord Bot
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# Discord Gemini Bot

A multimodal Discord bot powered by **Google Gemini 3** and **Veo** for text, image, and video generation.

## Features

- **Text Generation** - Conversational AI with context awareness
- **Vision Analysis** - Analyze and discuss images attached to messages
- **Image Generation** - Create images from text descriptions using Imagen
- **Video Generation** - Generate short videos using Veo 3.1

## Tech Stack

| Category        | Technology                       |
| --------------- | -------------------------------- |
| Runtime         | Python 3.12                      |
| Discord         | discord.py                       |
| AI Models       | Google Gemini 3, Imagen, Veo 3.1 |
| Type Checking   | Pyright                          |
| Package Manager | uv                               |
| Deployment      | Hugging Face Spaces (Docker)     |
| CI/CD           | GitHub Actions                   |

## Architecture

```
Discord User
    |
    v
Discord Gateway (WebSocket)
    |
    v
discord.py
    |
    v
Router (Intent Detection)
    |
    +---> Text Handler ---> Gemini 3 Pro
    |
    +---> Image Handler --> Imagen 3
    |
    +---> Video Handler --> Veo 3.1
```

### Project Structure

```
src/
├── main.py           # Entry point
├── config.py         # Environment configuration
├── app.py            # Gradio status page (HF Spaces)
├── ai/
│   ├── client.py     # Gemini API wrapper
│   └── models.py     # Model constants
├── bot/
│   ├── client.py     # Discord bot client
│   └── handlers.py   # Message routing & handlers
└── utils/
    └── logging.py    # Logger configuration
```

## Usage

Mention the bot or send a DM:

```
@Bot draw a sunset over mountains
@Bot video of a cat playing piano
@Bot explain this code [attach image]
@Bot what's the meaning of life?
```

### Intent Detection

The bot uses keyword-based routing (with AI-powered routing planned):

| Keywords                                  | Action           |
| ----------------------------------------- | ---------------- |
| "draw", "paint", "image of", "picture of" | Image generation |
| "video of", "animate", "movie of"         | Video generation |
| (default)                                 | Text generation  |

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Discord Bot Token
- Google AI API Key (Gemini)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/discord-bot.git
cd discord-bot

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your tokens
```

### Environment Variables

```env
DISCORD_TOKEN=your_discord_bot_token
GOOGLE_API_KEY=your_google_ai_api_key
USE_FUNCTION_CALLING=false
```

### Run Locally

```bash
uv run start
# or
python -m src.main
```

### Run Type Check

```bash
uv run pyright
```

## Deployment

This project is configured for **Hugging Face Spaces** with automatic deployment via GitHub Actions.

### CI/CD Pipeline

```
Push to main
    |
    v
GitHub Actions
    |
    +---> Pyright Type Check
    |
    v
Deploy to HF Spaces
```

### HF Spaces Setup

1. Create a new Space (Docker SDK, Private)
2. Add secrets: `DISCORD_TOKEN`, `GOOGLE_API_KEY`
3. Set up GitHub secrets: `HF_TOKEN`
4. Set up GitHub variables: `HF_USERNAME`, `HF_SPACE_NAME`

## Roadmap

- [x] Text generation with Gemini 3
- [x] Image analysis (vision)
- [x] Image generation with Imagen
- [x] Video generation with Veo
- [x] Modular architecture
- [x] Type checking with Pyright
- [x] CI/CD deployment
- [ ] AI-powered intent detection (function calling)
- [ ] Conversation history
- [ ] Slash commands

## Development Notes

Detailed development notes are available in `.dev-notes/`:

- `2025-11-24.md` - Architecture overview, WebSocket vs SSE comparison
- `2025-12-07.md` - Modularization and Router pattern
- `2025-12-09.md` - Type checking setup

## License

MIT
