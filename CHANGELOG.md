# Changelog

All notable changes to this project will be documented in this file.

## [1.3.0]

### Added
- Gradio web UI showing bot status (online/offline, user, guilds, uptime)
- `/healthz` endpoint for keep-alive pings

### Changed
- Switched deployment from Railway to Hugging Face Spaces
- Updated `setup-uv` GitHub Action from v4 to v7
- Refactored main entry point to run Gradio app alongside Discord bot

## [1.2.0]

### Added
- Conversation history support using sliding window strategy (last 10 bot-involved messages)
- New `src/bot/history.py` module for fetching conversation context
- Multi-turn conversation support - bot now understands follow-up messages

### Changed
- `generate_text()` now accepts conversation history for context-aware responses
- Text handler fetches recent bot interactions before generating response

## [1.1.0]

### Added
- System instruction with current date for text generation
- Optional Google Search grounding via `USE_GROUNDING` environment variable
- `USE_GROUNDING` option in `.env.example`

### Fixed
- Bot giving incorrect dates (was saying 2024 instead of 2025)
- Bot hallucinating information for real-time queries (CVEs, weather, news)
- Typo in `src/utils/__init__.py`: `setup_logger` → `setup_logging`

### Changed
- Text generation now includes system prompt with bot personality and current date
- Grounding can be enabled for real-time information retrieval

## [1.0.0] - 2025-12-09

### Added
- Initial release with Discord bot powered by Google Gemini 3
- Text generation with conversation support
- Image analysis (vision/multimodal)
- Image generation with Imagen 3
- Video generation with Veo 3.1
- Keyword-based intent routing
- Type checking with Pyright
- CI/CD deployment to Railway via GitHub Actions
- Custom logging with stdout/stderr routing
