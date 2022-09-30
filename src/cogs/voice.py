"""
Extension that includes voice functionality. Used to be a music bot,
now just tracks how long users were in a channel for.
"""

import datetime

import discord
from discord.ext import commands

import toof


class VoiceCog(commands.Cog):
    """Cog that watches for voice updates."""

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
        self.voiceusers: dict[int, datetime.datetime] = {}

        self.bot.tree.add_command(
            discord.app_commands.ContextMenu(
                name="Check Voice Time",
                callback=self.check_voice_time_context_callback
            )
        )

    async def cog_load(self):
        """Creates the dictionary when the cog is loaded with current voice users."""
        
        for guild in self.bot.guilds:
            for voice_channel in guild.voice_channels:
                for member in voice_channel.members:
                    self.voiceusers[member.id] = datetime.datetime.now()

    @commands.Cog.listener()
    async def on_resumed(self):
        """When the connection to discord is resumed, catches any voice updates the bot may have missed."""

        member_ids: list[int] = []
        for guild in self.bot.guilds:
            for voice_channel in guild.voice_channels:
                for member in voice_channel.members:
                    member_ids.append(member)

        for member_id in self.voiceusers.keys():
            if member_id not in member_ids:
                del self.voiceusers[member_id]

        for member_id in member_ids:
            if member_id not in self.voiceusers.keys():
                self.voiceusers[member_id] = datetime.datetime.now()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # Member joins a voice channel
        if after.channel and member.id not in self.voiceusers.keys():
            self.voiceusers[member.id] = datetime.datetime.now()
        # Member leaves voice
        if not after.channel and member.id in self.voiceusers.keys():
            del self.voiceusers[member.id]

    @discord.app_commands.guild_only()
    async def check_voice_time_context_callback(self, interaction: discord.Interaction, member: discord.Member):
        """Checks how long you've been in a voice channel"""
        
        if member.id not in self.voiceusers.keys():
            await interaction.response.send_message(content=f"{member.mention} isnt in a voice !", ephemeral=True)
            return

        delta = datetime.datetime.now() - self.voiceusers[member.id]

        seconds = delta.seconds
        days = delta.days

        hours = seconds // 3600
        seconds -= hours * 3600
        minutes = seconds // 60
        seconds -= minutes * 60

        string = f"woof! {member.mention} haz been in call for "
        if days > 0:
            string += f"{days} days, "
        string += f"{hours} hours, {minutes} mins, and {seconds} seconds"

        await interaction.response.send_message(content=string, ephemeral=True)
        
    
async def setup(bot: toof.ToofBot):
    await bot.add_cog(VoiceCog(bot))
    