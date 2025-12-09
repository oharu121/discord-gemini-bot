"""Message handlers and intent routing for Discord bot."""

import io
from abc import ABC, abstractmethod

import discord

from src.ai.client import GeminiClientWrapper
from src.utils.logging import logger


# --- Router Classes ---

class Router(ABC):
    """Base router interface for intent detection."""

    @abstractmethod
    async def detect_intent(self, prompt: str) -> str:
        """Detect user intent and return action type: 'text', 'image', or 'video'."""
        raise NotImplementedError


class KeywordRouter(Router):
    """Keyword-based intent detection (English only)."""

    VIDEO_KEYWORDS = ["video of", "animate", "movie of", "generate a video"]
    IMAGE_KEYWORDS = ["image of", "draw", "paint", "generate an image", "picture of"]

    async def detect_intent(self, prompt: str) -> str:
        """Detect intent based on keyword matching."""
        prompt_lower = prompt.lower()

        if any(kw in prompt_lower for kw in self.VIDEO_KEYWORDS):
            return "video"
        elif any(kw in prompt_lower for kw in self.IMAGE_KEYWORDS):
            return "image"
        return "text"


class FunctionCallingRouter(Router):
    """AI-powered intent detection using Gemini function calling (all languages)."""

    def __init__(self, ai_client: GeminiClientWrapper):
        self.ai = ai_client

    async def detect_intent(self, prompt: str) -> str:
        """
        Detect intent using Gemini function calling.

        TODO: Implement this method:
        1. Define tools (generate_video, generate_image, generate_text)
        2. Send prompt + tools to Gemini
        3. Parse Gemini's function call response
        4. Return the chosen function name
        """
        # Placeholder - falls back to text for now
        logger.warning("FunctionCallingRouter not implemented, defaulting to 'text'")
        raise NotImplementedError(
            "Function calling router not yet implemented. "
            "Set USE_FUNCTION_CALLING=false in .env"
        )


# --- Handler Functions ---

async def handle_video_generation(
    message: discord.Message,
    ai: GeminiClientWrapper,
    prompt: str
) -> None:
    """Handle video generation requests."""
    await message.add_reaction("\U0001F3A5")  # camera emoji
    status_msg = await message.reply(
        "Generating video with Veo... This usually takes ~1-2 minutes."
    )

    video_bytes = await ai.generate_video(prompt)

    if video_bytes:
        file = discord.File(io.BytesIO(video_bytes), filename="generation.mp4")
        await status_msg.delete()
        await message.reply(content=f"\U0001F3AC Video for: *{prompt}*", file=file)
    else:
        await status_msg.edit(content="\u274C Failed to generate video.")


async def handle_image_generation(
    message: discord.Message,
    ai: GeminiClientWrapper,
    prompt: str
) -> None:
    """Handle image generation requests."""
    from src.ai.models import MODEL_IMAGE

    await message.add_reaction("\U0001F3A8")  # art palette emoji

    img_bytes = await ai.generate_image(prompt)

    if img_bytes:
        file = discord.File(io.BytesIO(img_bytes), filename="generation.png")
        embed = discord.Embed(
            title="Generated Image",
            description=prompt,
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://generation.png")
        embed.set_footer(text=f"Model: {MODEL_IMAGE}")
        await message.reply(file=file, embed=embed)
    else:
        await message.reply("\u274C Could not generate image.")


async def handle_text_generation(
    message: discord.Message,
    ai: GeminiClientWrapper,
    prompt: str,
    image_data: list | None = None,
    bot_user: discord.User | discord.ClientUser | None = None
) -> None:
    """Handle text/reasoning requests (including vision)."""
    response_text = await ai.generate_text(prompt, image_data=image_data)

    # Split long messages (Discord limit is 2000 chars)
    if len(response_text) > 2000:
        chunks = [response_text[i:i + 1900] for i in range(0, len(response_text), 1900)]
        for chunk in chunks:
            await message.reply(chunk)
    else:
        await message.reply(response_text)

    # Update reactions
    if bot_user:
        await message.remove_reaction("\U0001F440", bot_user)  # eyes emoji
    await message.add_reaction("\u2705")  # checkmark emoji


async def process_message(
    message: discord.Message,
    ai: GeminiClientWrapper,
    router: Router,
    bot_user: discord.User | discord.ClientUser
) -> None:
    """Main message processing logic."""
    # Clean prompt: Remove bot mention
    prompt = message.content.replace(f"<@{bot_user.id}>", "").strip()

    if not prompt and not message.attachments:
        await message.channel.send("\U0001F44B Hi! Attach an image or ask me something.")
        return

    # UI Feedback
    async with message.channel.typing():
        await message.add_reaction("\U0001F440")  # eyes emoji - acknowledge receipt

        # Extract image attachments for multimodal
        image_inputs = []
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image"):
                    img_bytes = await attachment.read()
                    image_inputs.append({
                        "data": img_bytes,
                        "mime": attachment.content_type
                    })

        try:
            # Detect intent using router
            intent = await router.detect_intent(prompt)

            if intent == "video":
                await handle_video_generation(message, ai, prompt)
            elif intent == "image":
                await handle_image_generation(message, ai, prompt)
            else:
                await handle_text_generation(
                    message, ai, prompt,
                    image_data=image_inputs,
                    bot_user=bot_user
                )

        except Exception as e:
            logger.error(f"Processing Error: {e}")
            await message.reply(f"\u26A0\uFE0F An error occurred: {str(e)}")
