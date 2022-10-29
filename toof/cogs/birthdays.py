"""Extension that keeps track of people's birthdays within the server.
Includes a loop that checks to see if it is someone's birthday, a 
context menu for users to see others birthdays, and a command to set 
birthdays.
"""

import datetime

import discord
from discord.ext.commands import Cog 
from discord.ext.tasks import loop

import toof


class CheckBirthdayContext(discord.app_commands.ContextMenu):
    """Looks through the database for the given member and lets
    the caller know if it found anything.
    """

    def __init__(self, bot: toof.ToofBot):
        super().__init__(name="Check Birthday", callback=self.callback)
        self.bot = bot

    async def callback(
            self, interaction: discord.Interaction,
            member: discord.Member):
        
        birthday = await self.bot.get_birthday(member)
        if birthday is not None:
            await interaction.response.send_message(
                f"woof! ({birthday.strftime('%m/%d/%Y')})",
                ephemeral=True)
        else:
            await interaction.response.send_message(
                "idk ther bday!",
                ephemeral=True)
        

class BirthdayCommand(discord.app_commands.Command):
    """Allows users to add their birthdays to the database, or update
    it if it is already in the database.
    """

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="birthday",
            description="Tell Toof your birthday.",
            callback=self.callback)
        self.bot = bot

    @discord.app_commands.describe(birthday="Format as mm/dd/yyyy.")
    async def callback(self, interaction: discord.Interaction, birthday: str):
        
        try:
            # Parses string as datetime to make sure it is formatted
            # correctly.
            datetime.datetime.strptime(birthday, "%m/%d/%Y")
        except ValueError:
            await interaction.response.send_message(
                "woof! you gotta format as mm/dd/yyyy", 
                ephemeral=True)
            return
        
        if await self.bot.get_birthday(interaction.user) is not None:
            query = f"""
                UPDATE birthdays 
                SET birthday = '{birthday}' 
                WHERE user_id = {interaction.user.id}"""
        else:
            query = f"""
                INSERT INTO birthdays
                VALUES ({interaction.user.id}, '{birthday}')"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message("updooted !", ephemeral=True)
       

class BirthdayCog(Cog):

    def __init__(self, bot: toof.ToofBot):
        bot.tree.add_command(CheckBirthdayContext(bot))
        bot.tree.add_command(BirthdayCommand(bot))
        self.check_for_birthdays.start()
        self.bot = bot

    @loop(hours=12)
    async def check_for_birthdays(self):
        """Checks for birthdays and sends a happy birthday message to
        each guild's welcome channel that has users with birthdays in it.
        """

        # Only let the bot send bday messages in the AM
        now = datetime.datetime.now()
        if now.hour >= 12:
            return

        # Creates a list of users whose birthdays are today
        now = now.strftime("%m/%d/")
        query = f"SELECT user_id FROM birthdays WHERE birthday LIKE '{now}%'"
        async with self.bot.db.execute(query) as cursor:
            bday_users = [self.bot.get_user(row[0]) async for row in cursor]

        # Creates a dictionary keying a channel to a list of birthday
        # users in that channel's guild
        query = "SELECT welcome_channel_id FROM guilds"
        async with self.bot.db.execute(query) as cursor:
            chan_dict: dict[discord.TextChannel, list[discord.Member]] = {}
            async for row in cursor:
                channel = self.bot.get_channel(row[0])
                users_in_channel = [
                    member for member in bday_users
                    if member in channel.members
                ]
                if users_in_channel:
                    chan_dict[channel] = users_in_channel

        # Sends a message to each channel with birthday users
        for channel, members in chan_dict.items():
            content = ""
            for member in members:
                content += f"{member.mention} "
            content += "https://tenor.com/view/holiday-classics-elf-christmas-excited-happy-gif-15741376"

            await channel.send(content)


async def setup(bot: toof.ToofBot):
    await bot.add_cog(BirthdayCog(bot))
    