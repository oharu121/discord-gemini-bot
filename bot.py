import os
import io
import asyncio
import logging
from typing import Optional, List, Union

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Import the new Google GenAI SDK (supports Gemini 3 & Veo)
from google import genai
from google.genai import types

# --- Configuration ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GeminiBot")

# --- Constants ---
# Models based on Gemini 3 release info
MODEL_TEXT = "gemini-3-pro-preview" 
MODEL_IMAGE = "gemini-3-pro-image-preview" # Or "imagen-3.0-generate-002" if preferred
MODEL_VIDEO = "veo-3.1-generate-preview"

class GeminiClientWrapper:
    """Wrapper to handle Google GenAI interactions for Text, Image, and Video."""
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def generate_text(self, prompt: str, history: list = None, image_data: list = None) -> str:
        """Generates text, handling multimodal inputs (text + images)."""
        contents = []
        
        # Add history if provided
        if history:
            # Simple conversion of history to format expected by API
            # In production, manage full conversation turns here
            pass 

        # Add current images if any
        if image_data:
            for img in image_data:
                contents.append(types.Part.from_bytes(data=img['data'], mime_type=img['mime']))

        # Add text prompt
        contents.append(prompt)

        try:
            # Run in executor to avoid blocking the async event loop
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=MODEL_TEXT,
                contents=contents
            )
            return response.text
        except Exception as e:
            logger.error(f"Text Generation Error: {e}")
            return f"Error generating text: {str(e)}"

    async def generate_image(self, prompt: str) -> Optional[bytes]:
        """Generates an image using Gemini 3 Image Preview or Imagen."""
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_images,
                model=MODEL_IMAGE,
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            # Accessing the first generated image
            if response.generated_images:
                return response.generated_images[0].image.image_bytes
            return None
        except Exception as e:
            logger.error(f"Image Generation Error: {e}")
            raise e

    async def generate_video(self, prompt: str) -> Optional[bytes]:
        """Generates a video using Veo (Long running operation)."""
        logger.info(f"Starting video generation for: {prompt}")
        try:
            # Start the operation
            operation = await asyncio.to_thread(
                self.client.models.generate_videos,
                model=MODEL_VIDEO,
                prompt=prompt,
                config=types.GenerateVideosConfig(fps=24, duration_seconds=5) # Adjust config as needed
            )
            
            # Poll for completion
            # Note: In a real bot, you might want to offload polling to a background task
            # to prevent holding the connection open too long, but Veo is relatively fast.
            while not operation.done:
                logger.info("Waiting for video generation...")
                await asyncio.sleep(5)
                operation = await asyncio.to_thread(self.client.operations.get, operation.name)

            # Get result
            if operation.result and operation.result.generated_videos:
                 # Usually returns a URI or bytes depending on configuration
                 # For this example, we assume we need to download the bytes from the URI provided
                 # However, the SDK might provide bytes directly in some configs.
                 # Let's check typical Veo response structure:
                 video_result = operation.result.generated_videos[0]
                 return video_result.video.video_bytes
            return None
        except Exception as e:
            logger.error(f"Video Generation Error: {e}")
            raise e

class DiscordBot(discord.Client):
    def __init__(self):
        # Enable all intents as requested to read message content and members
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.ai = GeminiClientWrapper(GOOGLE_API_KEY)

    async def setup_hook(self):
        # Sync slash commands
        await self.tree.sync()
        logger.info("Slash commands synced.")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="mentions or /ask"))

    async def on_message(self, message):
        # Prevent infinite loops
        if message.author == self.user:
            return

        # Check if mentioned or in DM
        is_mentioned = self.user.mentioned_in(message)
        is_dm = isinstance(message.channel, discord.DMChannel)

        if is_mentioned or is_dm:
            await self.process_message(message)

    async def process_message(self, message):
        """Main logic for routing requests to Text, Image, or Video models."""
        
        # Clean prompt: Remove bot mention
        prompt = message.content.replace(f'<@{self.user.id}>', '').strip()
        if not prompt and not message.attachments:
            await message.channel.send("👋 Hi! Attach an image or ask me something.")
            return

        # UI Feedback
        async with message.channel.typing():
            await message.add_reaction('👀') # Acknowledge receipt

            # 1. Check for Attachments (Multimodal Vision)
            image_inputs = []
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith('image'):
                        # Download image bytes
                        img_bytes = await attachment.read()
                        image_inputs.append({'data': img_bytes, 'mime': attachment.content_type})

            # 2. Determine Intent (Simple Keyword Router)
            # In a production app, you might ask a cheap LLM (Gemini Flash) to classify the intent first.
            prompt_lower = prompt.lower()
            
            try:
                if any(x in prompt_lower for x in ["video of", "animate", "movie of", "generate a video"]):
                    # --- VIDEO GENERATION PATH ---
                    await message.add_reaction('🎥')
                    status_msg = await message.reply("Generating video with Veo... This usually takes ~1-2 minutes.")
                    
                    video_bytes = await self.ai.generate_video(prompt)
                    
                    if video_bytes:
                        file = discord.File(io.BytesIO(video_bytes), filename="generation.mp4")
                        await status_msg.delete()
                        await message.reply(content=f"🎬 Video for: *{prompt}*", file=file)
                    else:
                        await status_msg.edit(content="❌ Failed to generate video.")

                elif any(x in prompt_lower for x in ["image of", "draw", "paint", "generate an image", "picture of"]):
                    # --- IMAGE GENERATION PATH ---
                    await message.add_reaction('🎨')
                    
                    img_bytes = await self.ai.generate_image(prompt)
                    
                    if img_bytes:
                        file = discord.File(io.BytesIO(img_bytes), filename="generation.png")
                        embed = discord.Embed(title="Generated Image", description=prompt, color=discord.Color.blue())
                        embed.set_image(url="attachment://generation.png")
                        embed.set_footer(text=f"Model: {MODEL_IMAGE}")
                        await message.reply(file=file, embed=embed)
                    else:
                        await message.reply("❌ Could not generate image.")

                else:
                    # --- TEXT / REASONING PATH ---
                    # Handles standard chat + visual QA (if images attached)
                    response_text = await self.ai.generate_text(prompt, image_data=image_inputs)
                    
                    # Split long messages (Discord limit is 2000 chars)
                    if len(response_text) > 2000:
                        chunks = [response_text[i:i+1900] for i in range(0, len(response_text), 1900)]
                        for chunk in chunks:
                            await message.reply(chunk)
                    else:
                        await message.reply(response_text)
                    
                    await message.remove_reaction('👀', self.user)
                    await message.add_reaction('✅')

            except Exception as e:
                logger.error(f"Processing Error: {e}")
                await message.reply(f"⚠️ An error occurred: {str(e)}")

# --- Main Entry Point ---
if __name__ == "__main__":
    if not DISCORD_TOKEN or not GOOGLE_API_KEY:
        print("Error: Environment variables DISCORD_TOKEN or GOOGLE_API_KEY not found.")
    else:
        bot = DiscordBot()
        bot.run(DISCORD_TOKEN)