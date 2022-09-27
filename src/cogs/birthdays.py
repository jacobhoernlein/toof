"""
Extension that keeps track of people's birthdays within the server.
Includes a loop that checks to see if it is someone's birthday, a context
menu for users to see others birthdays, and a command to set birthdays.
"""

import json
from datetime import datetime

import discord
from discord.ext import commands, tasks

import toof


class BirthdayCog(commands.Cog):

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot

        with open('configs/birthdays.json') as fp:
            self.birthdays: dict[str, str] = json.load(fp)

        self.birthday_context = discord.app_commands.ContextMenu(
            name="Check Birthday",
            callback=self.birthday_context_callback
        )
        self.bot.tree.add_command(self.birthday_context)

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_day.start()

    def cog_unload(self):
        self.check_day.stop()

    @tasks.loop(hours=24)
    async def check_day(self):
        """Sends a birthday message on birthdays"""
        
        main_channel = self.bot.config.welcome_channel
        now = datetime.now().strftime("%m/%d/%Y")
        
        with open('configs/birthdays.json') as fp:
            birthdays:dict = json.load(fp)

        for user_id, birthday in birthdays.items():
            if now == birthday:
                user = self.bot.get_user(user_id)
                await main_channel.send(
                        f"{user.mention} https://tenor.com/view/holiday-classics-elf-christmas-excited-happy-gif-15741376"
                )

    async def birthday_context_callback(self, interaction: discord.Interaction, member: discord.Member):
        """Looks through the birthday file for the user and lets the user know if it found anything."""
        
        for user_id, birthday in self.birthdays.items():
            if str(member.id) == str(user_id):
                await interaction.response.send_message(f"woof! ({birthday})", ephemeral=True)
                return

        await interaction.response.send_message("idk ther bday!", ephemeral=True)
        
    @discord.app_commands.command(name="birthday", description="Tell Toof your birthday.")
    @discord.app_commands.describe(birthday="Format as mm/dd/yyyy.")
    async def birthday_update(self, interaction: discord.Interaction, birthday: str):
        """Allows users to add their birthdays to the file."""
        
        try:
            day = datetime.strptime(birthday, "%m/%d/%Y")
        # Formatting went wrong
        except ValueError:
            await interaction.response.send_message("woof! you gotta format as mm/dd/yyyy", ephemeral=True)
            return

        # Converts day from datetime object to string, stores in library
        day = day.strftime("%m/%d/%Y")
        self.birthdays[str(interaction.user.id)] = day

        with open("configs/birthdays.json", "w") as fp:
            json.dump(self.birthdays, fp, indent=4)

        await interaction.response.send_message("oki 👍", ephemeral=True)
          

async def setup(bot: toof.ToofBot):
    await bot.add_cog(BirthdayCog(bot))
    