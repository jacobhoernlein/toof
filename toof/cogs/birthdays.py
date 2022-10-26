"""Extension that keeps track of people's birthdays within the server.
Includes a loop that checks to see if it is someone's birthday, a 
context menu for users to see others birthdays, and a command to set 
birthdays.
"""

import datetime

import discord
from discord.ext import commands, tasks

import toof


class BirthdayCog(commands.Cog):
    """Cog that contains a loop to watch birthdays and commands
    relating to them.
    """

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
 
    async def cog_load(self):
        self.bot.tree.add_command(
            discord.app_commands.ContextMenu(
                name="Check Birthday",
                callback=self.birthday_context_callback))
        
        self.check_day.start()

    def cog_unload(self):
        self.check_day.stop()

    @tasks.loop(hours=12)
    async def check_day(self):
        """Sends a birthday message on birthdays"""

        # Only let the bot send bday messages in the AM
        now = datetime.datetime.now()
        if now.hour >= 12:
            return

        # Creates a list of users whose birthdays are today
        now = now.strftime("%m/%d")
        query = f"SELECT user_id FROM birthdays WHERE birthday LIKE '{now}%'"
        async with self.bot.db.execute(query) as cursor:
            bday_users = [self.bot.get_user(row[0]) async for row in cursor]

        # Creates a dictionary keying a channel to a list of birthday
        # users in that channel's guild
        query = "SELECT welcome_channel_id FROM guilds"
        async with self.bot.db.execute(query) as cursor:
            welcome_channels = {
                self.bot.get_channel(row[0]): [
                    member for member in bday_users 
                    if member in self.bot.get_channel(row[0]).members
                ] 
                async for row in cursor
            }

        # Sends a message to each channel with birthday users
        for channel, members in welcome_channels.items():
            if not members:
                continue

            content = ""
            for member in members:
                content += f"{member.mention} "
            content += "https://tenor.com/view/holiday-classics-elf-christmas-excited-happy-gif-15741376"

            await channel.send(content)

    async def birthday_context_callback(
            self, interaction: discord.Interaction, 
            member: discord.Member):
        """Looks through the birthdays table for the given member
        and lets the caller know if it found anything.
        """
        
        query = f"SELECT birthday FROM birthdays WHERE user_id = {member.id}"
        async with self.bot.db.execute(query) as cursor:
            row = await cursor.fetchone()

        if row is not None:
            await interaction.response.send_message(
                f"woof! ({row[0]})",
                ephemeral=True)
        else:
            await interaction.response.send_message(
                "idk ther bday!",
                ephemeral=True)

    @discord.app_commands.command(
        name="birthday",
        description="Tell Toof your birthday.")
    @discord.app_commands.describe(birthday="Format as mm/dd/yyyy.")
    async def birthday_command(
            self, interaction: discord.Interaction, 
            birthday: str):
        """Allows users to add their birthdays to the file."""
        
        # Ensures the birthday is formatted correctly.
        try:
            day = datetime.datetime.strptime(birthday, "%m/%d/%Y")
        except ValueError:
            await interaction.response.send_message(
                "woof! you gotta format as mm/dd/yyyy", 
                ephemeral=True
            )
            return
        else:
            day = day.strftime("%m/%d/%Y")
        
        query = f"SELECT * FROM birthdays WHERE user_id = {interaction.user.id}"
        async with self.bot.db.execute(query) as cursor:
            row = await cursor.fetchone()
            
        if row is not None:
            query = f"""
                UPDATE birthdays 
                SET birthday = '{day}' 
                WHERE user_id = {interaction.user.id}"""
            await self.bot.db.execute(query)
        else:
            query = f"""
                INSERT INTO birthdays
                VALUES ({interaction.user.id}, '{day}')"""
            await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message("updooted !", ephemeral=True)
       
          
async def setup(bot: toof.ToofBot):
    await bot.add_cog(BirthdayCog(bot))
    