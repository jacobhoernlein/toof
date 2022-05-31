"""Handles voice commands"""

import datetime as dt

import discord
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio
import youtube_dl as ytdl

class ToofVoice(commands.Cog):
    """Voice commands"""

    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.voiceusers = {}
        self.music_queue = []

        self.YDL_OPTIONS =  {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    # Starts loops
    @commands.Cog.listener()
    async def on_ready(self):
        self.check_voice.start()

    # Searches YouTube and returns a dict with URL and Title
    def search_yt(self, query:str):
        with ytdl.YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            except: 
                return None
            else:
                return {'url': info['formats'][0]['url'], 'title': info['title']}

    # Plays the next song in the queue
    def play_next(self, voice:discord.VoiceClient):
        if voice.is_playing():
            voice.stop()
        
        if len(self.music_queue) > 0:
            song = self.music_queue.pop(0)

            try:
                voice.play(
                    FFmpegPCMAudio(
                        song['url'],
                        **self.FFMPEG_OPTIONS
                    ),
                    after=lambda error: self.play_next(voice)
                )
            except:
                self.play_next(voice)
        
    # Joins the voice channel that the user is in
    # and plays some sick tunes
    @commands.command()
    async def play(self, ctx: commands.Context, *, search:str=None):
        """Resume paused music or add a YouTube video to the queue"""
        voice:discord.VoiceClient = ctx.voice_client
        if not voice:
            if ctx.author.voice:
                voice = await ctx.author.voice.channel.connect()
            else:
                await ctx.message.add_reaction("❓")
                return    

        if search:
            song = self.search_yt(search)
            if song:
                self.music_queue.append(song)
            else:
                await ctx.message.add_reaction("❓")
                return

            if not voice.is_playing():
                self.play_next(voice)
                await ctx.message.add_reaction("🎵")
            else:
                await ctx.message.add_reaction("👍")

        elif voice.is_paused():
            await ctx.message.add_reaction("▶️")
            voice.resume()
            return
        
        else:
            await ctx.message.add_reaction("❓")
        
    # Pauses the audio if there is any playing    
    @commands.command()
    async def pause(self, ctx: commands.Context):
        """Pause whatever Toof is saying"""
        voice:discord.VoiceClient = ctx.voice_client
        if not voice or not ctx.author.voice:
            await ctx.message.add_reaction("❓")
        elif voice.is_playing():
            await ctx.message.add_reaction("⏸️")
            voice.pause()
            
    # Skips the current song if the user has mod perms
    @commands.command()
    async def skip(self, ctx:commands.Context, number:int=None):
        """Skips to the next song or removes the specified song in the queue"""
        if self.bot.config.mod_role in ctx.author.roles:
            if number:
                self.music_queue.pop(number - 1)
                await ctx.message.add_reaction("👍")
            else:
                await ctx.message.add_reaction("⏩")
                self.play_next(ctx.voice_client)
        else:
            await ctx.message.add_reaction("❌")

    # Lists the queue
    @commands.command(aliases=["q"])
    async def queue(self, ctx:commands.Context):
        """Lists the queue"""
        if len(self.music_queue) < 1:
            return
        msg = "woof! (next up):\n"
        for i, song in enumerate(self.music_queue):
            msg += f"{i + 1}: {song['title']}\n"
        await ctx.send(msg)

    # Disconnects the voice client in the guild if there is one
    @commands.command()
    async def leave(self, ctx: commands.Context):
        """Removes Toof from the voice chat and clears the queue"""
        if ctx.voice_client:
            self.music_queue = []
            await ctx.voice_client.disconnect()
            await ctx.message.add_reaction("👍")
        else:
            await ctx.send("❓")

    @commands.command(aliases=["uptime"])
    async def voicetime(self, ctx:commands.Context):
        """Checks how long you've been in a voice channel"""
        if ctx.author not in self.voiceusers.keys():
            await ctx.message.add_reaction("❓")
            return

        delta:dt.timedelta = dt.datetime.now() - self.voiceusers[ctx.author]
        
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

        await ctx.send(string)

    # Adds member to active voice users list with the time they joined. Removes them if they leave
    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        if member == self.bot.user:
            return
        
        # Member joins a voice channel
        if not before.channel and after.channel:
            self.voiceusers[member] = dt.datetime.now()
        # Member leaves voice
        if before.channel and not after.channel:
            del self.voiceusers[member]

    # Checks all voice connections and disconnects
    # If there aren't any users
    @tasks.loop(seconds=30)
    async def check_voice(self):
        for voice in self.bot.voice_clients:
            if len(voice.channel.members) == 1 \
            or (not voice.is_playing() \
            and not voice.is_paused() \
            and len(self.music_queue) == 0):
                self.music_queue = []
                await voice.disconnect()
            

def setup(bot:commands.Bot):
    bot.add_cog(ToofVoice(bot))
