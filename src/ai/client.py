"""Google Gemini API client wrapper."""

import asyncio
from datetime import datetime

from google import genai
from google.genai import types

from src import config
from src.ai.models import MODEL_TEXT, MODEL_IMAGE, MODEL_VIDEO
from src.utils.logging import logger


class GeminiClientWrapper:
    """Wrapper to handle Google GenAI interactions for Text, Image, and Video."""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def generate_text(
        self,
        prompt: str,
        history: list[dict[str, str | list[str]]] | None = None,
        image_data: list | None = None
    ) -> str:
        """Generates text, handling multimodal inputs (text + images)."""
        contents: list[types.Content] = []

        # Add conversation history if provided (for multi-turn context)
        if history:
            for msg in history:
                role = msg["role"]
                parts = msg["parts"]
                # Convert to Gemini Content format
                if isinstance(role, str) and isinstance(parts, list):
                    contents.append(types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=str(p)) for p in parts]
                    ))

        # Build current message parts
        current_parts: list[types.Part] = []

        # Add current images if any
        if image_data:
            for img in image_data:
                current_parts.append(
                    types.Part.from_bytes(data=img["data"], mime_type=img["mime"])
                )

        # Add text prompt
        current_parts.append(types.Part.from_text(text=prompt))

        # Add current message as user turn
        contents.append(types.Content(role="user", parts=current_parts))

        # Build generation config with system instruction
        gen_config = types.GenerateContentConfig(
            system_instruction=f"""You are a helpful Discord bot assistant.
Today's date is {datetime.now().strftime("%Y-%m-%d")}.
Be concise in your responses as they appear in Discord chat.""",
        )

        # Add grounding if enabled (for real-time info like weather, news, CVEs)
        if config.USE_GROUNDING:
            gen_config.tools = [types.Tool(google_search=types.GoogleSearch())]

        try:
            # Run in executor to avoid blocking the async event loop
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=MODEL_TEXT,
                contents=contents,  # type: ignore[arg-type]
                config=gen_config
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"Text Generation Error: {e}")
            return f"Error generating text: {str(e)}"

    async def generate_image(self, prompt: str) -> bytes | None:
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
                image = response.generated_images[0].image
                if image:
                    return image.image_bytes
            return None
        except Exception as e:
            logger.error(f"Image Generation Error: {e}")
            raise e

    async def generate_video(self, prompt: str) -> bytes | None:
        """Generates a video using Veo (Long running operation)."""
        logger.info(f"Starting video generation for: {prompt}")
        try:
            # Start the operation
            operation = await asyncio.to_thread(
                self.client.models.generate_videos,
                model=MODEL_VIDEO,
                prompt=prompt,
                config=types.GenerateVideosConfig(fps=24, duration_seconds=5)
            )

            # Poll for completion
            while not operation.done:
                logger.info("Waiting for video generation...")
                await asyncio.sleep(5)
                operation = await asyncio.to_thread(
                    self.client.operations.get,
                    operation.name
                )

            # Get result
            result = getattr(operation, "result", None)
            if result and getattr(result, "generated_videos", None):
                video_result = result.generated_videos[0]
                video = getattr(video_result, "video", None)
                if video:
                    return video.video_bytes
            return None
        except Exception as e:
            logger.error(f"Video Generation Error: {e}")
            raise e
