"""Extension that includes voice functionality. Used to be a music bot,
now just tracks how long users were in a channel for.
"""

import datetime

import discord
from discord.ext import commands

from .. import base


class VoiceCog(base.Cog):
    """Cog that watches for voice updates."""

    def __init__(self, bot: base.Bot):
        self.bot = bot
        self.id_time_dict: dict[int, datetime.datetime] = {}

    async def cog_load(self):
        """Creates the dictionary when the cog is loaded with current
        voice users.
        """

        self.bot.tree.add_command(
            discord.app_commands.ContextMenu(
                name="Check Voice Time",
                callback=self.check_voice_callback))

        self.id_time_dict = {}
        for guild in self.bot.guilds:
            for voice_channel in guild.voice_channels:
                for member in voice_channel.members:
                    self.id_time_dict[member.id] = datetime.datetime.now()

    @commands.Cog.listener()
    async def on_resumed(self):
        """When the connection to discord is resumed, catches any voice
        updates the bot may have missed.
        """

        # Creates a list of all members currently in a voice channel
        current_member_ids: list[int] = []
        for guild in self.bot.guilds:
            for voice_channel in guild.voice_channels:
                for member in voice_channel.members:
                    current_member_ids.append(member.id)

        # Deletes all members from the dict who are no longer connected
        ids_to_delete = [
            member_id for member_id in self.id_time_dict 
            if member_id not in current_member_ids]
        for id in ids_to_delete:
            del self.id_time_dict[id]

        # Adds all members to the dict who need to be added
        ids_to_add = [
            member_id for member_id in current_member_ids
            if member_id not in self.id_time_dict]
        for id in ids_to_add:
            self.id_time_dict[id] = datetime.datetime.now()

    @commands.Cog.listener()
    async def on_voice_state_update(
            self, member: discord.Member, 
            before: discord.VoiceState, after: discord.VoiceState):
        """Handles users joining or leaving a channel
        by updating the internal dict.
        """
        
        # Member joins a voice channel
        if after.channel and member.id not in self.id_time_dict:
            self.id_time_dict[member.id] = datetime.datetime.now()
        # Member leaves voice
        if not after.channel and member.id in self.id_time_dict:
            del self.id_time_dict[member.id]

    @discord.app_commands.guild_only()
    async def check_voice_callback(
            self, interaction: discord.Interaction,
            member: discord.Member):
        """Checks how long a given user has been in a voice channel."""
        
        if member.id not in self.id_time_dict:
            await interaction.response.send_message(
                content=f"{member.mention} isnt in a voice !", 
                ephemeral=True)
            return

        delta = datetime.datetime.now() - self.id_time_dict[member.id]

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

        await interaction.response.send_message(
            content=string,
            ephemeral=True)
        