"""Extension that includes small features that did not fit into other
extensions. Ping command, status changes, happy friday, etc.
"""

import datetime
from random import choice

import discord
from discord.ext.commands import Cog
from discord.ext.tasks import loop

import toof


class PingCommand(discord.app_commands.Command):
    """Equivelant of the ping command."""

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="speak",
            description="Check Toof's latency.",
            callback=self.callback)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"woof! ({round(self.bot.latency * 1000)}ms)",
            ephemeral=True)


class AvatarCommand(discord.app_commands.Command):

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="avatar",
            description="Get a user's avatar.",
            callback=self.callback)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.send_message(user.avatar.url)


class MiscCog(Cog):

    def __init__(self, bot: toof.ToofBot):
        bot.tree.add_command(PingCommand(bot))
        bot.tree.add_command(AvatarCommand(bot))
        self.change_status.start()
        self.check_day.start()
        self.bot = bot

    @loop(seconds=180)
    async def change_status(self):
        """Changes the bot's status on a 180s loop"""

        activities = [
            discord.Activity(
                type=discord.ActivityType.watching,
                name="the mailman"),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="you pee"),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="bees"),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="february face"),
            discord.Activity(
                type=discord.ActivityType.playing,
                name="with a ball")
        ]

        await self.bot.change_presence(activity=choice(activities))

    @loop(hours=12)
    async def check_day(self):
        """Sends a good morning happy friday gif at certain time"""
        
        # Only let the bot send the message on Fridays in the AM
        now = datetime.datetime.now()
        if now.weekday() != 4 or now.hour >= 12:
            return

        query = "SELECT welcome_channel_id FROM guilds"
        async with self.bot.db.execute(query) as cursor:
            async for row in cursor:
                try:
                    await self.bot.get_channel(row[0]).send("https://tenor.com/view/happy-friday-good-morning-friday-morning-gif-13497103")
                except (AttributeError, discord.HTTPException):
                    # Either the channel couldn't be found or couldn't
                    # send to the channel.
                    pass

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author == self.bot.user:
            return
        
        if "car ride" in msg.content.lower():
            await msg.channel.send("WOOF.")
        elif "good boy" in msg.content.lower():
            await msg.channel.send("WOOF.")

        if (msg.mentions and msg.reference
            and not msg.author.bot
            and not msg.reference.cached_message.author.bot):

            await msg.add_reaction(self.bot.toofping_emote)
                     

    @Cog.listener()
    async def on_reaction_add(
            self, reaction: discord.Reaction,
            user: discord.User):
        if (reaction.message.reference is not None
            and reaction.message.mentions
            and reaction.emoji == self.bot.toofping_emote
            and self.bot.user in [member async for member in reaction.users()]
            and user == reaction.message.reference.cached_message.author):
            
            await reaction.message.reply(
                "https://tenor.com/view/discord-reply-discord-reply-off-discord-reply-gif-22150762")
            await reaction.message.remove_reaction(
                reaction.emoji, self.bot.user)


async def setup(bot: toof.ToofBot):
    await bot.add_cog(MiscCog(bot))
    