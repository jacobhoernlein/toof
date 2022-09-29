"""
Extension that keeps track of people's birthdays within the server.
Includes a loop that checks to see if it is someone's birthday, a context
menu for users to see others birthdays, and a command to set birthdays.
"""

from datetime import datetime

import discord
from discord.ext import commands, tasks

import toof


class BirthdayCog(commands.Cog):

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
        self.birthday_context = discord.app_commands.ContextMenu(
            name="Check Birthday",
            callback=self.birthday_context_callback
        )
        self.bot.tree.add_command(self.birthday_context)

    async def cog_load(self):
        self.check_day.start()

    def cog_unload(self):
        self.check_day.stop()

    @tasks.loop(hours=24)
    async def check_day(self):
        """Sends a birthday message on birthdays"""
        
        now = datetime.now().strftime("%m/%d/%Y")
        
        async with self.bot.db.execute('SELECT * FROM birthdays') as cursor:
            birthday_list = await cursor.fetchall()

            for birthday_item in birthday_list:
                user_id: int = birthday_item[0]
                birthday: str = birthday_item[1]

                if now == birthday:
                    user = self.bot.get_user(user_id)
                    
                    for guild in self.bot.guilds:
                        if user in guild.members:

                            await cursor.execute(f'SELECT welcome_channel_id FROM guilds WHERE guild_id = {guild.id}')
                            channel_id = await cursor.fetchone()

                            channel = discord.utils.find(lambda c: c.id == channel_id, guild.channels)

                            await channel.send(
                                f"{user.mention} https://tenor.com/view/holiday-classics-elf-christmas-excited-happy-gif-15741376"
                            )

    async def birthday_context_callback(self, interaction: discord.Interaction, member: discord.Member):
        """Looks through the birthday file for the user and lets the user know if it found anything."""
        
        async with self.bot.db.execute('SELECT * FROM birthdays') as cursor:
            birthday_list = await cursor.fetchall()

        for birthday_item in birthday_list:
            user_id: int = birthday_item[0]
            birthday: str = birthday_item[1]
            
            if member.id == user_id:
                await interaction.response.send_message(f"woof! ({birthday})", ephemeral=True)
                return

        await interaction.response.send_message("idk ther bday!", ephemeral=True)
        
    @discord.app_commands.command(name="birthday", description="Tell Toof your birthday.")
    @discord.app_commands.describe(birthday="Format as mm/dd/yyyy.")
    async def birthday_update(self, interaction: discord.Interaction, birthday: str):
        """Allows users to add their birthdays to the file."""
        
        # Ensures the birthday is formatted correctly.
        try:
            datetime.strptime(birthday, "%m/%d/%Y")
        # Formatting went wrong
        except ValueError:
            await interaction.response.send_message("woof! you gotta format as mm/dd/yyyy", ephemeral=True)
            return

        async with self.bot.db.execute('SELECT * FROM birthdays') as cursor:
            user_ids = [record[0] for record in await cursor.fetchall()]
            
        user_id = interaction.user.id

        if user_id in user_ids:
            await self.bot.db.execute(f'UPDATE birthdays SET birthday = \'{birthday}\' WHERE user_id = {user_id}',)
        else:
            await self.bot.db.execute(f'INSERT INTO birthdays VALUES ({user_id}, \'{birthday}\')')

        await self.bot.db.commit()

        await interaction.response.send_message("updooted !", ephemeral=True)
          

async def setup(bot: toof.ToofBot):
    await bot.add_cog(BirthdayCog(bot))
    