"""Configuration module for Discord Gemini Bot."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required credentials
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Feature flags
USE_FUNCTION_CALLING = os.getenv("USE_FUNCTION_CALLING", "false").lower() == "true"


def validate_config() -> bool:
    """Validate that required configuration is present."""
    missing = []
    if not DISCORD_TOKEN:
        missing.append("DISCORD_TOKEN")
    if not GOOGLE_API_KEY:
        missing.append("GOOGLE_API_KEY")

    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        return False
    return True
