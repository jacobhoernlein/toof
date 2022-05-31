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
        self.voice:discord.VoiceClient = None
        self.voiceusers = {}
        
        self.music_queue = []

        self.YDL_OPTIONS =  {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    # Starts loops
    @commands.Cog.listener()
    async def on_ready(self):
        self.check_voice.start()

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

    # Searches YouTube and returns a dict with URL and Title
    def search_yt(self, query:str):
        with ytdl.YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            except: 
                return None
            return {'url': info['formats'][0]['url'], 'title': info['title']}

    # Plays the next song in the queue until it's empty
    def play_song(self):
        if len(self.music_queue) > 0:
            song = self.music_queue.pop(0)
            self.current_song = song

            self.voice.play(
                FFmpegPCMAudio(
                    song['url'],
                    **self.FFMPEG_OPTIONS
                ),
                after=lambda e: self.play_song()
            )      

    # Lists the queue
    @commands.command(aliases=["q"])
    async def queue(self, ctx:commands.Context):
        """Lists the queue"""
        if len(self.music_queue) == 0:
            await ctx.send("...")
        else:
            msg = "woof! (next up):\n"
            for i, song in enumerate(self.music_queue):
                msg += f"{i + 1}: {song['title']}\n"
            await ctx.send(msg)

    # Joins the voice channel that the user is in
    # and plays some sick tunes
    @commands.command()
    async def play(self, ctx: commands.Context, *, search:str=None):
        """Resume paused music or add a YouTube video to the queue"""
        if not self.voice:
            if ctx.author.voice and search:
                self.voice = await ctx.author.voice.channel.connect()
            else:
                await ctx.message.add_reaction("❓")
                return    

        if search:
            song = self.search_yt(search)
            if song is not None:
                self.music_queue.append(song)
            else:
                await ctx.message.add_reaction("❓")
                return

            if not self.voice.is_playing():
                await ctx.message.add_reaction("🎵")
                self.play_song() 
            else:
                await ctx.message.add_reaction("👍")

        elif self.voice.is_paused():
            await ctx.message.add_reaction("▶️")
            self.voice.resume()
            return
        
        else:
            await ctx.message.add_reaction("❓")
        
    # Pauses the audio if there is any playing    
    @commands.command()
    async def pause(self, ctx: commands.Context):
        """Pause whatever Toof is saying"""
        if not self.voice or not ctx.author.voice:
            await ctx.message.add_reaction("❓")
        elif self.voice.is_playing():
            await ctx.message.add_reaction("⏸️")
            self.voice.pause()
            
    # Skips the current song if the user has mod perms
    @commands.command()
    async def skip(self, ctx:commands.Context, number:int=None):
        """Skips to the next song or removes the specified song in the queue"""
        if self.bot.config.mod_role in ctx.author.roles:
            if self.voice:
                if number is not None:
                    try:
                        self.music_queue.pop(number - 1)
                    except:
                        await ctx.message.add_reaction("❓")
                    else:
                        await ctx.message.add_reaction("👍")
                else:
                    await ctx.message.add_reaction("⏩")
                    if self.voice.is_playing():
                        self.voice.stop()
                    self.play_song()
            else:
                await ctx.message.add_reaction("❓")
        else:
            await ctx.message.add_reaction("❌")

    # Disconnects the voice client in the guild if there is one
    @commands.command()
    async def leave(self, ctx: commands.Context):
        """Removes Toof from the voice chat and clears the queue"""
        if self.bot.config.mod_role in ctx.author.roles:
            if self.voice:
                await self.voice.disconnect()
                await ctx.message.add_reaction("👍")
            else:
                await ctx.message.add_reaction("❓")
        else:
            await ctx.message.add_reaction("❌")

    # Adds member to active voice users list with the time they joined. Removes them if they leave
    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        # Member joins a voice channel
        if not before.channel and after.channel:
            self.voiceusers[member] = dt.datetime.now()
        # Member leaves voice
        if before.channel and not after.channel:
            try:
                del self.voiceusers[member]
            except KeyError:
                print(f"Could not delete {member} from voiceusers. Skipping")
            if member == self.bot.user:
                self.music_queue = []
                self.voice = None
                
        if self.voice:
            if len(self.voice.channel.members) == 1:
                await self.voice.disconnect()
                
    # Checks all voice connections and disconnects
    # If there aren't any users
    @tasks.loop(seconds=15)
    async def check_voice(self):
        if not self.voice:
            return

        if len(self.voice.channel.members) == 1:
            await self.voice.disconnect()
            

def setup(bot:commands.Bot):
    bot.add_cog(ToofVoice(bot))
