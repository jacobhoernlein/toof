"""Handles voice commands"""

import datetime
import discord
import toof


async def setup(bot: toof.ToofBot):

    # Watches for when member joins or leaves voice, then updates the dictionary.
    @bot.event
    async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # Member joins a voice channel
        if after.channel and member.id not in bot.config.voiceusers.keys():
            bot.config.voiceusers[member.id] = datetime.datetime.now()
        # Member leaves voice
        if not after.channel and member.id in bot.config.voiceusers.keys():
            del bot.config.voiceusers[member.id]

    @bot.tree.context_menu(name="Check Voice Time")
    @discord.app_commands.guild_only()
    async def check_voice_time(interaction: discord.Interaction, member: discord.Member):
        """Checks how long you've been in a voice channel"""
        
        if member.id not in bot.config.voiceusers.keys():
            await interaction.response.send_message(content=f"{member.mention} isn't in a voice channel!", ephemeral=True)
            return

        delta:datetime.timedelta = datetime.datetime.now() - bot.config.voiceusers[member.id]
        
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
        