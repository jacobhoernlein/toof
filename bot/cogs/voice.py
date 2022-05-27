"""Handles voice commands"""

import discord
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio

class ToofVoice(commands.Cog):
    """Voice commands"""

    def __init__(self, bot:commands.Bot):
        self.bot = bot

    # Starts loops
    @commands.Cog.listener()
    async def on_ready(self):
        self.check_voice.start()

    # Joins the voice channel that the user is in
    # and plays some sick tunes
    @commands.command()
    async def play(self, ctx: commands.Context, track='it_has_to_be_this_way'):
        """Connect Toof to a voice channel to play a noise"""
        voice:discord.VoiceClient = ctx.voice_client
        if not voice:
            if not ctx.author.voice:
                await ctx.send("*tilts head*")
                return
            else:
                voice = await ctx.author.voice.channel.connect()
        
        if voice.is_playing():
            voice.stop()

        if voice.is_paused():
            voice.resume()
            return

        source = FFmpegPCMAudio(f'./attachments/audio/{track}.wav')
        voice.play(source)
        await ctx.send("woof 🎵")

    # Pauses the audio if there is any playing    
    @commands.command()
    async def pause(self, ctx: commands.Context):
        """Pause whatever Toof is saying"""
        voice:discord.VoiceClient = ctx.voice_client
        if not voice:
            await ctx.send("*sniffs butt*")
            return
        if voice.is_playing():
            voice.pause()

    # Disconnects the voice client in the guild if there is one
    @commands.command(aliases=["shutup"])
    async def leave(self, ctx: commands.Context):
        """Removes Toof from the voice chat"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        else:
            await ctx.send("...?")

    # Checks all voice connections and disconnects
    # If there aren't any users or if it is not playing
    @tasks.loop(seconds=10)
    async def check_voice(self):
        for voice in self.bot.voice_clients:
            if len(voice.channel.members) == 1:
                await voice.disconnect()
            elif not voice.is_playing() and not voice.is_paused():
                await voice.disconnect()
        

def setup(bot:commands.Bot):
    bot.add_cog(ToofVoice(bot))
