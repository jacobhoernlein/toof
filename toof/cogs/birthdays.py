"""Extension that keeps track of people's birthdays within the server.
Includes a loop that checks to see if it is someone's birthday, a 
context menu for users to see others birthdays, and a command to set 
birthdays.
"""

import datetime

import discord
from discord.ext import tasks

from .. import base


class BirthdayCog(base.Cog):
    """Cog that contains a loop to watch birthdays and commands
    relating to them.
    """
 
    async def cog_load(self):
        self.bot.tree.add_command(
            discord.app_commands.ContextMenu(
                name="Check Birthday",
                callback=self.birthday_context_callback))
        
        self.check_day.start()

    def cog_unload(self):
        self.check_day.stop()

    @tasks.loop(hours=24)
    async def check_day(self):
        """Sends a birthday message on birthdays"""
        
        # Creates a list of users whose birthdays are today
        now = datetime.datetime.now().strftime("%m/%d")
        query = f"SELECT user_id FROM birthdays WHERE birthday LIKE '{now}%'"
        async with self.bot.db.execute(query) as cursor:
            bday_users = [self.bot.get_user(row[0]) async for row in cursor]

        # Loops over every welcome channel and sends a message
        # to every birthday boy in that server
        query = "SELECT welcome_channel_id FROM guilds"
        async with self.bot.db.execute(query) as cursor:
            async for row in cursor:
                
                welcome_channel = self.bot.get_channel(row[0])
                if welcome_channel is None:
                    continue

                # Creates a list of users that have a birthday 
                # and are in the current guild
                bday_users_in_guild = [
                    user for user in bday_users
                    if user in welcome_channel.guild.members]
                if not bday_users_in_guild:
                    continue

                content = ""
                for user in bday_users_in_guild:
                    content += f"{user.mention} "
                content += "https://tenor.com/view/holiday-classics-elf-christmas-excited-happy-gif-15741376"

                await welcome_channel.send(content)

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
            query = f"UPDATE birthdays SET birthday = '{day}' WHERE user_id = {interaction.user.id}"
            await self.bot.db.execute(query)
        else:
            query = f"INSERT INTO birthdays VALUES ({interaction.user.id}, '{day}')"
            await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message("updooted !", ephemeral=True)
          