"""
Extension that includes small features that did not fit into
other extensions. Ping command, status changes, happy friday, etc.
"""

import datetime
from random import choice

import discord
from discord.ext import commands, tasks

import toof


class MiscCog(commands.Cog):
    """Cog that contains basic event handling"""

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.change_status.start()
        self.check_time.start()

    def cog_unload(self):
        self.change_status.cancel()
        self.check_time.cancel()

    @tasks.loop(seconds=180)
    async def change_status(self):
        """Changes the status on a 180s loop"""

        await self.bot.change_presence(activity=choice(self.bot.config.activities))

    @tasks.loop(seconds=60)
    async def check_time(self):
        """Sends a good morning happy friday gif at certain time"""
        
        main_channel = self.bot.config.main_channel
        now = datetime.datetime.now()
    
        # Automated messages will be sent at noon
        if now.hour == 12 and now.minute == 00:
            # Checks to see if it's Friday
            if now.weekday() == 4:
                await main_channel.send("https://tenor.com/view/happy-friday-good-morning-friday-morning-gif-13497103")

    # Replies to messages that have certain phrases in them    
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author == self.bot.user:
            return
        
        # Responds to messages with certain phrases
        content = msg.content
        if "car ride" in content.lower():
            print("CAR RIDE?")
            await msg.channel.send("WOOF.")
        elif "good boy" in content.lower():
            print("I'M A GOOD BOY!!")
            await msg.channel.send("WOOF.")
        elif "Connor" in content:
            await msg.channel.send("connor*")

        # Handles ping replies
        if msg.mentions and msg.reference:
            if msg.reference.cached_message.author.bot:
                return
            emoji = discord.utils.find(lambda e : e.name == 'toofping', msg.guild.emojis)
            if emoji:
                await msg.add_reaction(emoji)
            else:
                await msg.add_reaction("🇵")
                await msg.add_reaction("🇮")
                await msg.add_reaction("🇳")
                await msg.add_reaction("🇬")            
                    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, usr: discord.User):
        # If this was a ping reply situation, replies to the offender then removes the bot's reaction.

        if reaction.message.mentions and reaction.message.reference \
        and reaction.emoji.name == 'toofping' \
        and self.bot.user in [member async for member in reaction.users()]:
            if reaction.message.reference.cached_message.author == usr:
                await reaction.message.reply(f"https://tenor.com/view/discord-reply-discord-reply-off-discord-reply-gif-22150762")
                await reaction.message.remove_reaction(reaction.emoji, self.bot.user)

    @discord.app_commands.command(name="speak", description="Check Toof's latency.")
    async def speak(self, interaction: discord.Interaction):
        """Equivelant of the ping command."""
        
        await interaction.response.send_message(f"woof! ({round(self.bot.latency * 1000)}ms)", ephemeral=True)

    
async def setup(bot: toof.ToofBot):
    await bot.add_cog(MiscCog(bot))
