import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class HelpView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=60)
        self.embeds = embeds
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.children[0].disabled = self.current_page == 0 # Previous button
        self.children[1].disabled = self.current_page == len(self.embeds) - 1 # Next button

    @discord.ui.button(label='◀️', style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label='▶️', style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Shows a list of available commands.")
    async def help(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        all_commands = self.bot.tree.get_commands()
        
        # Filtering commands is complex with app commands. For now, we list them all.
        # A proper implementation would check user's permissions against command's required permissions.
        
        pages = []
        chunk_size = 10
        
        # Sort commands alphabetically for consistent pagination
        sorted_commands = sorted(all_commands, key=lambda cmd: cmd.name)

        for i in range(0, len(sorted_commands), chunk_size):
            chunk = sorted_commands[i:i + chunk_size]
            embed = discord.Embed(title=f"Help - Page {len(pages) + 1}/{len(sorted_commands) // chunk_size + (1 if len(sorted_commands) % chunk_size > 0 else 0)}", color=discord.Color.blue())
            for command in chunk:
                embed.add_field(name=f"/{command.name}", value=command.description or "No description", inline=False)
            pages.append(embed)

        if not pages:
            await interaction.followup.send("No commands found.")
            return

        view = HelpView(pages)
        message = await interaction.followup.send(embed=pages[0], view=view)
        view.message = message # Store message to edit on timeout


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
