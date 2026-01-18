"""Discord bot client."""

import aiohttp
import discord
from discord import app_commands

from src import config
from src.ai.client import GeminiClientWrapper
from src.ai.rag import RAGClient, format_response_with_sources
from src.bot.handlers import (
    KeywordRouter,
    FunctionCallingRouter,
    process_message
)
from src.utils.logging import logger


def create_connector_with_custom_dns() -> aiohttp.TCPConnector:
    """Create aiohttp connector with custom DNS resolver (Google/Cloudflare)."""
    try:
        from aiohttp.resolver import AsyncResolver
        resolver = AsyncResolver(nameservers=["8.8.8.8", "1.1.1.1"])
        logger.info("Using custom DNS resolver (Google/Cloudflare)")
        return aiohttp.TCPConnector(resolver=resolver)
    except Exception as e:
        logger.warning(f"Failed to create custom DNS resolver: {e}, using default")
        return aiohttp.TCPConnector()


class DiscordBot(discord.Client):
    """Main Discord bot client with Gemini AI integration."""

    def __init__(self, connector: aiohttp.TCPConnector | None = None):
        # Enable all intents to read message content and members
        intents = discord.Intents.all()
        super().__init__(intents=intents, connector=connector)

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

        # RAG client for knowledge base queries
        self.rag = RAGClient(config.RAG_API_URL)

        # Register slash commands
        self._register_commands()

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

    def _register_commands(self) -> None:
        """Register slash commands with the command tree."""

        @self.tree.command(name="ask", description="Query the knowledge base")
        async def ask_command(interaction: discord.Interaction, query: str) -> None:
            """
            Handle /ask slash command for RAG queries.

            Args:
                interaction: Discord interaction
                query: User's question to the knowledge base
            """
            await interaction.response.defer()

            response_text = ""
            chunks: list[dict] = []
            followup_message: discord.WebhookMessage | None = None
            last_update_len = 0
            update_threshold = 100  # Update every ~100 chars

            try:
                async for event_type, data in self.rag.query(query):
                    if event_type == "chunks":
                        chunks = data  # type: ignore[assignment]
                    elif event_type == "token":
                        response_text += data  # type: ignore[operator]

                        # Update message periodically to show streaming
                        if len(response_text) - last_update_len >= update_threshold:
                            display_text = response_text + "..."
                            if len(display_text) > 2000:
                                display_text = display_text[:1997] + "..."

                            if followup_message:
                                await followup_message.edit(content=display_text)
                            else:
                                followup_message = await interaction.followup.send(
                                    display_text
                                )
                            last_update_len = len(response_text)

                    elif event_type == "done":
                        # Final update with sources
                        final_text = format_response_with_sources(
                            response_text, chunks
                        )
                        if len(final_text) > 2000:
                            final_text = final_text[:1997] + "..."

                        if followup_message:
                            await followup_message.edit(content=final_text)
                        else:
                            await interaction.followup.send(final_text)

                    elif event_type == "error":
                        error_msg = f"Error querying knowledge base: {data}"
                        if followup_message:
                            await followup_message.edit(content=error_msg)
                        else:
                            await interaction.followup.send(error_msg)
                        return

            except Exception as e:
                logger.error(f"Error in /ask command: {e}")
                error_msg = "An error occurred while querying the knowledge base."
                if followup_message:
                    await followup_message.edit(content=error_msg)
                else:
                    await interaction.followup.send(error_msg)
