from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
import requests
import base64
import io
import discord
import logging

load_dotenv()

AI_API_KEY = os.getenv('AI_API_KEY')
URL = "https://ai.hackclub.com/proxy/v1/chat/completions"

class AI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @app_commands.command(name="generate-image", description="Generates an image using Nano Banana 3 Pro.")
    @app_commands.describe(prompt="The prompt.")
    async def image_gen(self, ctx: commands.Context, prompt: str) -> None:
        """Generates an image using Nano Banana 3 Pro."""
        await ctx.response.defer()

        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "google/gemini-2.5-flash-image",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "modalities": ["image", "text"],
            "image_config": {
                "aspect_ratio": "16:9"
            }
        }

        response = await self.bot.loop.run_in_executor(
            None,
            lambda: requests.post(URL, headers=headers, json=payload)
        )
        result = response.json()
        # Log a summary of the API response, avoiding large data like base64 image strings.
        self.logger.info("API response for prompt '%s'. Contains choices: %s", prompt, 'choices' in result)


        # The generated image will be in the assistant message
        if result.get("choices"):
            message = result["choices"][0]["message"]
            if message.get("images"):
                # Assuming one image
                image_url = message["images"][0]["image_url"]["url"]  # Base64 data URL
                self.logger.info("Generated image URL (truncated) for prompt '%s': %s", prompt, image_url[:50])

                try:
                    # Handle data URI prefix
                    if "," in image_url:
                        base64_data = image_url.split(",")[1]
                    else:
                        base64_data = image_url

                    image_bytes = base64.b64decode(base64_data)
                    image_file = io.BytesIO(image_bytes)
                    await ctx.followup.send(file=discord.File(image_file, "image.png"))
                    self.logger.info("Successfully sent image for prompt: '%s'", prompt)
                    return # Exit after sending the image
                except (base64.binascii.Error, IndexError) as e:
                    self.logger.error("Error decoding base64 for prompt '%s': %s", prompt, e)
                    await ctx.followup.send("I couldn't generate an image. The API returned invalid image data.")
                    return

        # If we reach here, no image was found or there was an error
        # Log a summary of the API response when no image is found, avoiding large data.
        self.logger.error("API returned no image for prompt '%s'. Full response summary: %s", prompt, {'status_code': response.status_code, 'response_keys': list(result.keys()), 'choices_present': 'choices' in result})
        await ctx.followup.send("I couldn't generate an image. The API returned no image.")

async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))