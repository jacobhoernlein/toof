"""
Extension that includes voice functionality. Used to be a music bot,
now just tracks how long users were in a channel for.
"""

from datetime import datetime, timedelta

import discord
from discord.ext import commands

import toof


class VoiceCog(commands.Cog):

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
        self.voiceusers: dict[int, datetime] = {}

        self.check_voice_time_context = discord.app_commands.ContextMenu(
            name="Check Voice Time",
            callback=self.check_voice_time_callback
        )
        self.bot.tree.add_command(self.check_voice_time_context)

    @commands.Cog.listener()
    async def on_ready(self):
        for voice_channel in self.bot.config.server.voice_channels:
            for member in voice_channel.members:
                self.voiceusers[member.id] = datetime.now()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # Member joins a voice channel
        if after.channel and member.id not in self.voiceusers.keys():
            self.voiceusers[member.id] = datetime.now()
        # Member leaves voice
        if not after.channel and member.id in self.voiceusers.keys():
            del self.voiceusers[member.id]

    @discord.app_commands.guild_only()
    async def check_voice_time_callback(self, interaction: discord.Interaction, member: discord.Member):
        """Checks how long you've been in a voice channel"""
        
        if member.id not in self.voiceusers.keys():
            await interaction.response.send_message(content=f"{member.mention} isn't in a voice channel!", ephemeral=True)
            return

        delta: timedelta = datetime.now() - self.voiceusers[member.id]
        
        seconds = delta.seconds
        days = delta.days

        hours = seconds // 3600
        seconds -= hours * 3600
        minutes = seconds // 60
        seconds -= minutes * 60

        string = f"woof! {member.mention} has been in call for "
        if days > 0:
            string += f"{days} days, "
        string += f"{hours} hours, {minutes} minutes, and {seconds} seconds."

        await interaction.response.send_message(content=string, ephemeral=True)
        
    
async def setup(bot: toof.ToofBot):
    await bot.add_cog(VoiceCog(bot))