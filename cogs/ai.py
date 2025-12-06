import base64
import io
import logging
import os
import random
from pathlib import Path

import discord
import requests
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import json
from datetime import datetime
import asyncio

load_dotenv()

PERSONALITY = [
    "discord zoomer",
    "potter head",
    "roasting mode",
    "'You are absolutely right' mode",
]
AI_API_KEY = os.getenv("AI_API_KEY")
URL = "https://ai.hackclub.com/proxy/v1/chat/completions"
USAGE_FILE = Path(__file__).parent / "ai_usage.json"
DAILY_LIMIT = 20


async def ai_commands_check(interaction: discord.Interaction) -> bool:
    cog = interaction.client.get_cog("AI")
    if not cog:
        # This is an unlikely scenario, but a good safeguard.
        raise app_commands.CheckFailure("The AI cog is not loaded.")

    # 1. API Key Check
    if not AI_API_KEY:
        raise app_commands.CheckFailure(":x: The AI API key is not configured. Please set the `AI_API_KEY` in the `.env` file.")

    # 2. Usage Limit Check
    if not await cog.check_and_increment_usage():
        raise app_commands.CheckFailure(f":x: The daily AI command limit of {DAILY_LIMIT} has been reached. Please try again tomorrow.")
    
    return True

class AI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.usage_lock = asyncio.Lock()

    async def check_and_increment_usage(self) -> bool:
        async with self.usage_lock:
            self.logger.info(f"Checking AI usage limit. Usage file path: {USAGE_FILE.absolute()}")
            try:
                with open(USAGE_FILE, "r") as f:
                    data = json.load(f)
                self.logger.info(f"Loaded usage data: {data}")
            except (FileNotFoundError, json.JSONDecodeError):
                self.logger.info("Usage file not found or invalid. Initializing new data.")
                data = {"date": "", "count": 0}

            today = datetime.now().strftime("%Y-%m-%d")

            if data["date"] != today:
                self.logger.info("New day detected. Resetting usage count.")
                data["date"] = today
                data["count"] = 1
            elif data["count"] >= DAILY_LIMIT:
                self.logger.warning(f"AI daily limit reached. Count: {data['count']}")
                return False
            else:
                data["count"] += 1
                self.logger.info(f"Incrementing AI usage count to: {data['count']}")

            try:
                # Use a more explicit write, flush, and close sequence for debugging
                f = open(USAGE_FILE, "w")
                json.dump(data, f)
                f.flush()
                os.fsync(f.fileno()) # Force write to disk
                f.close()
                self.logger.info(f"Successfully wrote and synced updated usage data: {data}")
            except Exception as e:
                self.logger.error(f"Failed to write to usage file: {e}", exc_info=True)
            
            return True

    @app_commands.command(
        name="generate-image", description="Generates an image using Nano Banana 3 Pro."
    )
    @app_commands.describe(prompt="The prompt.")
    @app_commands.check(ai_commands_check)
    async def image_gen(self, interaction: discord.Interaction, prompt: str) -> None:
        """Generates an image using Nano Banana 3 Pro."""
        await interaction.response.defer()

        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "google/gemini-2.5-flash-image",
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["image", "text"],
            "image_config": {"aspect_ratio": "16:9"},
        }

        response = await self.bot.loop.run_in_executor(
            None, lambda: requests.post(URL, headers=headers, json=payload)
        )
        result = response.json()
        # Log a summary of the API response, avoiding large data like base64 image strings.
        self.logger.info(
            "API response for prompt '%s'. Contains choices: %s",
            prompt,
            "choices" in result,
        )

        # The generated image will be in the assistant message
        if result.get("choices"):
            message = result["choices"][0]["message"]
            if message.get("images"):
                # Assuming one image
                image_url = message["images"][0]["image_url"]["url"]  # Base64 data URL
                self.logger.info(
                    "Generated image URL (truncated) for prompt '%s': %s",
                    prompt,
                    image_url[:50],
                )

                try:
                    # Handle data URI prefix
                    if "," in image_url:
                        base64_data = image_url.split(",")[1]
                    else:
                        base64_data = image_url

                    image_bytes = base64.b64decode(base64_data)
                    image_file = io.BytesIO(image_bytes)
                    await interaction.followup.send(file=discord.File(image_file, "image.png"))
                    self.logger.info("Successfully sent image for prompt: '%s'", prompt)
                    return  # Exit after sending the image
                except (base64.binascii.Error, IndexError) as e:
                    self.logger.error(
                        "Error decoding base64 for prompt '%s': %s", prompt, e
                    )
                    await interaction.followup.send(
                        "I couldn't generate an image. The API returned invalid image data."
                    )
                    return

        # If we reach here, no image was found or there was an error
        # Log a summary of the API response when no image is found, avoiding large data.
        self.logger.error(
            "API returned no image for prompt '%s'. Full response summary: %s",
            prompt,
            {
                "status_code": response.status_code,
                "response_keys": list(result.keys()),
                "choices_present": "choices" in result,
            },
        )
        await interaction.followup.send(
            "I couldn't generate an image. The API returned no image."
        )

    @app_commands.command(name="ask-ai", description="Ask AI a question.")
    @app_commands.describe(prompt="The prompt.")
    @app_commands.check(ai_commands_check)
    async def ask_ai(self, interaction: discord.Interaction, prompt: str) -> None:
        """Ask AI a question."""
        await interaction.response.defer()

        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        try:
            response = await self.bot.loop.run_in_executor(
                None, lambda: requests.post(URL, headers=headers, json=payload)
            )
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            result = response.json()
            self.logger.info(
                "API response for prompt '%s'. Contains choices: %s",
                prompt,
                "choices" in result,
            )

            if result.get("choices") and result["choices"][0]["message"].get("content"):
                content = result["choices"][0]["message"]["content"]
                await interaction.followup.send(content)
                self.logger.info(
                    "Successfully sent AI response for prompt: '%s'", prompt
                )
            else:
                self.logger.error(
                    "API returned no content for prompt '%s'. Full response summary: %s",
                    prompt,
                    {
                        "status_code": response.status_code,
                        "response_keys": list(result.keys()),
                        "choices_present": "choices" in result,
                    },
                )
                await interaction.followup.send("I couldn't get a response from the AI.")

        except requests.exceptions.RequestException as e:
            self.logger.error("Request to AI API failed for prompt '%s': %s", prompt, e)
            await interaction.followup.send(f"Failed to communicate with the AI API: {e}")
        except Exception as e:
            self.logger.error(
                "An unexpected error occurred in ask_ai for prompt '%s': %s", prompt, e
            )
            await interaction.followup.send("An unexpected error occurred while asking the AI.")

    @app_commands.command(
        name="ask-ai-with-personality",
        description="Ask AI a question with a random personality.",
    )
    @app_commands.describe(prompt="The prompt.")
    @app_commands.check(ai_commands_check)
    async def ask_ai_with_personality(self, interaction: discord.Interaction, prompt: str) -> None:
        """Ask AI a question with a random personality."""
        await interaction.response.defer()

        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {
                    "role": "system",
                    "content": f"Act like a {random.choice(PERSONALITY)}",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }

        try:
            response = await self.bot.loop.run_in_executor(
                None, lambda: requests.post(URL, headers=headers, json=payload)
            )
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            result = response.json()
            self.logger.info(
                "API response for prompt '%s'. Contains choices: %s",
                prompt,
                "choices" in result,
            )

            if result.get("choices") and result["choices"][0]["message"].get("content"):
                content = result["choices"][0]["message"]["content"]
                await interaction.followup.send(content)
                self.logger.info(
                    "Successfully sent AI response for prompt: '%s'", prompt
                )
            else:
                self.logger.error(
                    "API returned no content for prompt '%s'. Full response summary: %s",
                    prompt,
                    {
                        "status_code": response.status_code,
                        "response_keys": list(result.keys()),
                        "choices_present": "choices" in result,
                    },
                )
                await interaction.followup.send("I couldn't get a response from the AI.")

        except requests.exceptions.RequestException as e:
            self.logger.error("Request to AI API failed for prompt '%s': %s", prompt, e)
            await interaction.followup.send(f"Failed to communicate with the AI API: {e}")
        except Exception as e:
            self.logger.error(
                "An unexpected error occurred in ask_ai for prompt '%s': %s", prompt, e
            )
            await interaction.followup.send("An unexpected error occurred while asking the AI.")


async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))
