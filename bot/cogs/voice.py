"""Handles voice commands"""

import datetime as dt
import discord
import toof


async def setup(bot:toof.ToofBot):
    voiceusers = {}

    @bot.event
    async def on_voice_state_update(member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        # Member joins a voice channel
        if not before.channel and after.channel:
            voiceusers[member] = dt.datetime.now()
        # Member leaves voice
        if before.channel and not after.channel:
            try:
                del voiceusers[member]
            except KeyError:
                print(f"Could not delete {member} from voiceusers. Skipping")

    @bot.tree.context_menu(name="Check Voice Time")
    @discord.app_commands.guild_only()
    async def check_voice_time(interaction:discord.Interaction, member:discord.Member):
        """Checks how long you've been in a voice channel"""
        if member not in voiceusers.keys():
            await interaction.response.send_message(content="❓", ephemeral=True)
            return

        delta:dt.timedelta = dt.datetime.now() - voiceusers[member]
        
        seconds = delta.seconds
        days = delta.days

        hours = seconds // 3600
        seconds -= hours * 3600
        minutes = seconds // 60
        seconds -= minutes * 60

        string = "woof! ("
        if days > 0:
            string += f"{days}d, "
        string += f"{hours}h, {minutes}m, {seconds}s)"

        await interaction.response.send_message(content=string, ephemeral=True)
        