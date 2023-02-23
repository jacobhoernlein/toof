"""Extension that includes voice functionality. Used to be a music bot,
now just tracks how long users were in a channel for.
"""

import datetime

import discord
from discord.ext.commands import Cog
from num2words import num2words

import toof


class VoiceConfig(discord.app_commands.Group):

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="voice",
            description="Configure voice channel category.")
        self.bot = bot

    @discord.app_commands.command(
        name="disable",
        description="Disable automatic channel updates.")
    async def disable_command(self, interaction: discord.Interaction):
        query = f"""
            UPDATE guilds
            SET voice_category_id = 0
            WHERE guild_id = {interaction.guild_id}"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            "Channel Category Log disabled.", ephemeral=True)
    
    @discord.app_commands.command(
        name="set",
        description="Set the voice channel category to update.")
    async def set_command(self, interaction: discord.Interaction, id: str):
        
        try:
            id = int(id)
        except ValueError:
            await interaction.response.send_message(
                "Enter ID as integer.", ephemeral=True)
            return

        query = f"""
            UPDATE guilds
            SET voice_category_id = {id}
            WHERE guild_id = {interaction.guild_id}"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            f"Channel Category set.", ephemeral=True)
        
    @discord.app_commands.command(
        name="create",
        description="Create a new category for voice channels.")
    async def create_command(self, interaction: discord.Interaction):
        category = await interaction.guild.create_category("Voice Channels")
        await category.create_voice_channel("voice one")

        query = f"""
            UPDATE guilds
            SET voice_category_id = {category.id}
            WHERE guild_id = {interaction.guild_id}"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            "Channel Category created.", ephemeral=True)


class CheckVoiceContext(discord.app_commands.ContextMenu):
    """Checks how long a given user has been in a voice channel."""

    def __init__(
            self, bot: toof.ToofBot,
            id_time_dict: dict[int, datetime.datetime]):
        super().__init__(name="Check Voice Time", callback=self.callback)
        self.guild_only = True
        self.bot = bot
        self.id_time_dict = id_time_dict

    async def callback(
            self, interaction: discord.Interaction,
            member: discord.Member):
        
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


class VoiceCog(Cog):

    def __init__(self, bot: toof.ToofBot):
        
        now = datetime.datetime.now()
        self.id_time_dict: dict[int, datetime.datetime] = {}
        for guild in bot.guilds:
            for voice_channel in guild.voice_channels:
                for member in voice_channel.members:
                    self.id_time_dict[member.id] = now
        
        bot.tree.add_command(CheckVoiceContext(bot, self.id_time_dict))
        self.bot = bot
         
    @Cog.listener()
    async def on_resumed(self):
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

    @Cog.listener()
    async def on_voice_state_update(
            self, member: discord.Member, 
            _, after: discord.VoiceState):
        
        # Member joins a voice channel
        if after.channel and member.id not in self.id_time_dict:
            self.id_time_dict[member.id] = datetime.datetime.now()
            
        # Member leaves voice
        if not after.channel and member.id in self.id_time_dict:
            del self.id_time_dict[member.id]

        # Get the empty channels for the guild's category
        # If it doesn't exist, simply return.
        category = await self.bot.get_category(member.guild)
        if not isinstance(category, discord.CategoryChannel):
            return
        empty_channels = [c for c in category.voice_channels if not c.members]
        
        # Add an empty channel since all channels are full.
        if not empty_channels:
            await category.create_voice_channel(
                f"voice {num2words(len(category.voice_channels) + 1)}")

        # Delete an empty channel since 2 are empty.
        if len(empty_channels) >= 2:
            del_channel = empty_channels[-1]
            await del_channel.delete()

            # Rename and reorder leftover channels.
            for i, channel in enumerate([
                c for c in category.voice_channels
                if c != del_channel]):
                
                await channel.edit(
                    name=f"voice {num2words(i + 1)}",
                    position=i)

    
async def setup(bot: toof.ToofBot):
    await bot.add_cog(VoiceCog(bot))
    