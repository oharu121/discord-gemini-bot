"""Discord bot client."""

import discord
from discord import app_commands

from src import config
from src.ai.client import GeminiClientWrapper
from src.bot.handlers import (
    KeywordRouter,
    FunctionCallingRouter,
    process_message
)
from src.utils.logging import logger


class DiscordBot(discord.Client):
    """Main Discord bot client with Gemini AI integration."""

    def __init__(self):
        # Enable all intents to read message content and members
        intents = discord.Intents.all()
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

        # Config is validated in main.py before DiscordBot is created
        assert config.GOOGLE_API_KEY is not None
        self.ai = GeminiClientWrapper(config.GOOGLE_API_KEY)

        # Select router based on config
        if config.USE_FUNCTION_CALLING:
            self.router = FunctionCallingRouter(self.ai)
            logger.info("Using FunctionCallingRouter (AI-powered intent detection)")
        else:
            self.router = KeywordRouter()
            logger.info("Using KeywordRouter (keyword-based intent detection)")

    async def setup_hook(self) -> None:
        """Called once when the bot starts."""
        await self.tree.sync()
        logger.info("Slash commands synced.")

    async def on_ready(self) -> None:
        """Called when bot is fully connected."""
        if self.user:
            logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="mentions or /ask"
            )
        )

    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming messages."""
        # Prevent infinite loops - also guard against self.user being None
        if not self.user or message.author == self.user:
            return

        # Check if mentioned or in DM
        is_mentioned = self.user.mentioned_in(message)
        is_dm = isinstance(message.channel, discord.DMChannel)

        if is_mentioned or is_dm:
            await process_message(message, self.ai, self.router, self.user)
