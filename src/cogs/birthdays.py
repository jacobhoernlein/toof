"""
Extension that keeps track of people's birthdays within the server.
Includes a loop that checks to see if it is someone's birthday, a context
menu for users to see others birthdays, and a command to set birthdays.
"""

import datetime

import discord
from discord.ext import commands, tasks

import toof


class BirthdayCog(commands.Cog):

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
        
        self.bot.tree.add_command(
            discord.app_commands.ContextMenu(
                name="Check Birthday",
                callback=self.birthday_context_callback
            )
        )

    async def cog_load(self):
        self.check_day.start()

    def cog_unload(self):
        self.check_day.stop()

    @tasks.loop(hours=24)
    async def check_day(self):
        """Sends a birthday message on birthdays"""
        
        # Creates a list of users whose birthdays are today
        now = datetime.datetime.now().strftime("%m/%d")
        async with self.bot.db.execute(f'SELECT user_id FROM birthdays WHERE birthday LIKE \'{now}%\'') as cursor:
            bday_users = [self.bot.get_user(record[0]) async for record in cursor]

        # Loops over every welcome channel and sends a message to every birthday boy in that server
        async with self.bot.db.execute('SELECT welcome_channel_id FROM guilds') as cursor:
            async for record in cursor:
                welcome_channel = self.bot.get_channel(record[0])
                if welcome_channel is None:
                    continue

                bday_users_in_guild = [user for user in bday_users if user in welcome_channel.guild.members]
                if len(bday_users_in_guild) == 0:
                    continue

                content = ""
                for user in bday_users_in_guild:
                    content += f"{user.mention} "
                content += "https://tenor.com/view/holiday-classics-elf-christmas-excited-happy-gif-15741376"

                await welcome_channel.send(content)

    async def birthday_context_callback(self, interaction: discord.Interaction, member: discord.Member):
        """Looks through the birthday file for the user and lets the user know if it found anything."""
        
        async with self.bot.db.execute(f'SELECT birthday FROM birthdays WHERE user_id = {member.id}') as cursor:
            record = await cursor.fetchone()

        if record:
            await interaction.response.send_message(f"woof! ({record[0]})", ephemeral=True)
        else:
            await interaction.response.send_message("idk ther bday!", ephemeral=True)

    @discord.app_commands.command(name="birthday", description="Tell Toof your birthday.")
    @discord.app_commands.describe(birthday="Format as mm/dd/yyyy.")
    async def birthday_update(self, interaction: discord.Interaction, birthday: str):
        """Allows users to add their birthdays to the file."""
        
        # Ensures the birthday is formatted correctly.
        try:
            day = datetime.datetime.strptime(birthday, "%m/%d/%Y")
        # Formatting went wrong
        except ValueError:
            await interaction.response.send_message("woof! you gotta format as mm/dd/yyyy", ephemeral=True)
            return
        else:
            day = day.strftime("%m/%d/%Y")
        
        async with self.bot.db.execute('SELECT user_id FROM birthdays') as cursor:
            user_ids = [record[0] async for record in cursor]
            
        if interaction.user.id in user_ids:
            await self.bot.db.execute(
                f'UPDATE birthdays SET birthday = \'{day}\' WHERE user_id = {interaction.user.id}'
            )
        else:
            await self.bot.db.execute(
                f'INSERT INTO birthdays VALUES ({interaction.user.id}, \'{day}\')'
            )
        await self.bot.db.commit()

        await interaction.response.send_message("updooted !", ephemeral=True)
          

async def setup(bot: toof.ToofBot):
    await bot.add_cog(BirthdayCog(bot))
    