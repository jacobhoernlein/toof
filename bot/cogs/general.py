"""Basic commands for Toof"""

import json
import os
import datetime as dt
from random import choice
from typing import Union

from PIL import Image
import pillow_heif
import discord
from discord.ext import commands, tasks
import deepl

import toof

def days_to_age(days:int) -> str:
    """Returns a formatted date based on the inputted days"""
    if days < 1:
            years = 0
            months = 0
            days = 0
    else:
        years = int(days / 365.25)
        days -= int(years * 365.25)
        months = int(days / 30.437)
        days -= int(months * 30.437)

    age_str = ""
    if years > 0:
        age_str += f"{years}y"
        if months > 0 or days > 0:
            age_str += " "
    if months > 0:
        age_str += f"{months}m"
        if days > 0:
            age_str += " "
    age_str += f"{days}d"

    return age_str

class ToofCommands(commands.Cog):
    """Basic general commands for Toof"""

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
        self.toofpics = []

        for filename in os.listdir('attachments'):
            self.toofpics.append(f'attachments/{filename}')

        with open('configs/birthdays.json') as fp:
            self.birthdays:dict = json.load(fp)

    # Equivalent of "ping" command that other bots have
    # Gives the latency, and if the user is in a voice channel,
    # Connects to that channel and plays a funny noise
    @commands.command(aliases=["ping"])
    async def speak(self, ctx: commands.Context):
        """Equivalent of \"ping\" command"""
        await ctx.send(f"woof. ({round(self.bot.latency * 1000)}ms)")
           
    # Makes Toof curl up in the users lap.
    # Shuts down the bot if called by Jacob
    @commands.command(aliases=["shutdown"])
    async def sleep(self, ctx: commands.Context):
        """Make Toof take a nap"""
        # Makes sure only I can disable the bot
        if ctx.author.id == 243845903146811393:
            await ctx.send('*fucking dies*')
            await self.bot.toof_shut_down()
        # Kindly lets the user know they can't do that
        else:
            await ctx.send(f"*snuggles in {ctx.author.display_name}'s lap*")

    # Sends a random picture of Toof
    @commands.group(aliases=["picture"])
    async def pic(self, ctx: commands.Context):
        """Sends a random toofpic"""
        if not ctx.invoked_subcommand: 
            filename = choice(self.toofpics)
            with open(filename, 'rb') as fp:
                pic = discord.File(fp, filename=filename)
                await ctx.send(file=pic)

    # Adds a toofpic to the folder
    @pic.command(name="add", hidden=True)
    async def pic_add(self, ctx: commands.Context):
        """Adds a picture to toof pics folder"""
        if ctx.author.id != 243845903146811393:
            await ctx.message.add_reaction("❌")
            return

        if not ctx.message.attachments:
            await ctx.message.add_reaction("❓")
            return
        
        fileaddress = f'attachments/{len(self.toofpics) + 1}.jpg'

        file:discord.Attachment = ctx.message.attachments[0]

        # No conversion necessary, saves directly
        if file.filename.lower().endswith('.jpg'):
            with open(fileaddress, 'wb') as fp:
                await file.save(fp)

            self.toofpics.append(fileaddress)
            await ctx.message.add_reaction("👍")
        # Converts image from png to jpg, then saves it
        elif file.filename.lower().endswith('.png'):
            with open('temp.png', 'wb') as fp:
                await file.save(fp)

            png = Image.open('temp.png')
            jpg = png.convert('RGB')
            jpg.save(fileaddress)
            os.remove('temp.png')

            self.toofpics.append(fileaddress)
            await ctx.message.add_reaction("👍")
        # Converts HEIC to jpg, then saves it
        elif file.filename.lower().endswith('.heic'):
            with open('temp.heic', 'wb') as fp:
                await file.save(fp)

            with open('temp.heic', 'rb') as fp:    
                heif_file = pillow_heif.open_heif(fp)
            image = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                'raw',
            )
            image.save(fileaddress)
            os.remove('temp.heic')

            self.toofpics.append(fileaddress)
            await ctx.message.add_reaction("👍")
        # Can't convert other formats
        else:
            await ctx.message.add_reaction("👎")

    # Adds a message to the quoteboard
    @commands.command()
    async def quote(self, ctx: commands.Context, member:Union[discord.Member, str]=None, *, quote:str=None):
        """
        Adds something to the quoteboard\n
        You can either use this in a reply to an original message,
        Or you can use it by doing: 
            'toof, quote \"the person's name\" {the quote body}'
        """

        quote_channel = self.bot.config.quotes_channel

        # If the command is a reply, adds the original message to the quoteboard
        if ctx.message.reference:
            message = ctx.message.reference.cached_message

            if message:
                if message.content:
                    embed = discord.Embed(
                        description=message.content,
                        color=discord.Color.blurple()
                    )
                else:
                    embed = discord.Embed(colour=discord.Colour.blurple())
                if message.attachments:
                    attachment_url = message.attachments[0].url
                    embed.set_image(url=attachment_url)

                embed.set_author(
                    name=f"{message.author.name}#{message.author.discriminator} (click to jump):",
                    url=message.jump_url,
                    icon_url=message.author.avatar_url
                )
        
                date = message.created_at.strftime("%m/%d/%Y")
                embed.set_footer(text=date)

            else:
                await ctx.message.add_reaction("👎")
                return
        # If it is not a reply, uses the normal functionality
        else:
            if member is None or quote is None:
                await ctx.message.add_reaction("❓")
                return
            
            embed = discord.Embed(
                description=quote,
                color=discord.Color.blurple()
            )

            if isinstance(member, discord.Member):
                embed.set_author(
                    name=f"{member.name}#{member.discriminator} (allegedly) (click to jump):",
                    url=ctx.message.jump_url,
                    icon_url=member.avatar_url
                )
            elif isinstance(member, str):
                embed.set_author(
                    name=f"{member} (allegedly) (click to jump):",
                    url=ctx.message.jump_url
                )
            else:
                await ctx.message.add_reaction("❓")
                return
            
            if ctx.message.attachments:
                attachment_url = ctx.message.attachments[0].url
                embed.set_image(url=attachment_url)
            
            date = ctx.message.created_at.strftime("%m/%d/%Y")
            embed.set_footer(text=date)

        await quote_channel.send(
            content=f"{ctx.author.mention} submitted a quote:",
            embed=embed
        )

    # Shows someone's birthday
    @commands.group(invoke_without_command=True)
    async def bday(self, ctx:commands.Context, member:discord.Member=None):
        """
        Looks up a members birthday. Or, use subcommands 
        to add or remove your own, or to lookup someone's 
        age on discord.
        """            
        if member is None:
            member = ctx.author
        
        for user_id, birthday in self.birthdays.items():
            if str(member.id) == str(user_id):
                age = dt.datetime.now() - dt.datetime.strptime(birthday, "%m/%d/%Y")
            
                await ctx.send(f"woof! ({birthday} -> {days_to_age(age.days)}!)")
        
                return
        await ctx.send("...")

    # Adds someone's birthday to the config
    @bday.command(name="add")
    async def bday_add(self, ctx:commands.Context, birthday:str=None):
        """Add your birthday to the list"""
        # Checks to make sure a user hasn't already set their birthday
        for user_id in self.birthdays.keys():
            if str(ctx.author.id) == str(user_id):
               await ctx.message.add_reaction("👎")
               return

        try:
            day = dt.datetime.strptime(birthday, "%m/%d/%Y")
        # Formatting went wrong
        except:
            await ctx.message.add_reaction("❓")
            await ctx.send("woof! (mm/dd/yyyy)")
            return

        day = day.strftime("%m/%d/%Y")

        self.birthdays[str(ctx.author.id)] = day
        with open("configs/birthdays.json", "w") as fp:
            json.dump(self.birthdays, fp, indent=4)

        await ctx.message.add_reaction("👍")

    # Removes someone's birthday from the config
    @bday.command()
    async def remove(self, ctx:commands.Context):
        """Remove your birthday from the list"""
        for user_id in self.birthdays.keys():
            if str(ctx.author.id) == str(user_id):
                await ctx.message.add_reaction("👍")

                del self.birthdays[str(user_id)]                
                with open("configs/birthdays.json", "w") as fp:
                    json.dump(self.birthdays, fp, indent=4)
                
                return
        await ctx.message.add_reaction("❓")

    # Shows someone's age on Discord
    @bday.command(name="discord")
    async def discord_age(self, ctx:commands.Context, member:discord.Member=None):
        """Gives the members Discord age"""
        if member is None:
            member = ctx.author
        
        date_str = member.created_at.strftime("%m/%d/%Y")
        age:dt.timedelta = dt.datetime.now() - member.created_at
        
        await ctx.send(f"woof! ({date_str} -> {days_to_age(age.days)}!)")

class ToofEvents(commands.Cog):
    """Cog that contains basic event handling"""

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
        self.translator = deepl.Translator(os.getenv('DEEPLKEY'))
        
        with open('configs/birthdays.json') as fp:
            self.birthdays:dict = json.load(fp)

    # Starts loops
    @commands.Cog.listener()
    async def on_ready(self):
        self.change_status.start()
        self.check_time.start()

    @commands.Cog.listener()
    async def on_member_join(self, member:discord.Member):
        """Sends a message to the welcome channel when a new member joins"""
        welcome_channel = self.bot.config.welcome_channel
        rules_channel = self.bot.config.rules_channel

        await welcome_channel.send(
            f"henlo {member.mention} welcime to server. read {rules_channel.mention} pls. say 'woof' when ur done 🐶"
        )

    # Replies to messages that have certain phrases in them    
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        """Listens for specific messages"""

        # Ignores messages sent by the bot and messages sent in the welcome channel
        if msg.author == self.bot.user or msg.channel == self.bot.config.welcome_channel:
            return
        
        # Responds to messages with certain phrases
        content = msg.content
        if "car ride" in content.lower():
            print("CAR RIDE?")
            await msg.channel.send("WOOF.")
        elif "good boy" in content.lower():
            print("I'M A GOOD BOY!!")
            await msg.channel.send("WOOF.")
        elif "Connor" in content:
            await msg.channel.send("connor*")

        # Handles ping replies
        if msg.mentions and msg.reference:
            emoji = discord.utils.find(lambda e : e.name == 'toofping', msg.guild.emojis)
            if emoji:
                await msg.add_reaction(emoji)
            else:
                await msg.add_reaction("🇵")
                await msg.add_reaction("🇮")
                await msg.add_reaction("🇳")
                await msg.add_reaction("🇬")            
        
    # Translates messages using DeepL API
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction:discord.Reaction, user:discord.Member):
        # Ignore reactions added by the bot
        if user == self.bot.user:
            return

        # Translates to English using DeepL API
        if reaction.emoji == '🇬🇧' or reaction.emoji == '🇺🇸' and reaction.count == 1:
            result = self.translator.translate_text(str(reaction.message.content), target_lang="EN-US")
            await reaction.message.reply(f'{result.detected_source_lang} -> EN: "{result.text}"')
            return
        # Translates to Japanese using DeepL API
        if reaction.emoji == '🇯🇵' and reaction.count == 1:
            result = self.translator.translate_text(str(reaction.message.content), target_lang="JA")
            await reaction.message.reply(f'{result.detected_source_lang} -> JA: "{result.text}"')
            return
                    
    # Changes the status on a loop
    @tasks.loop(seconds=180)
    async def change_status(self):
        """Changes the status on a 180s loop"""
        await self.bot.change_presence(activity=choice(self.bot.config.activities))

    # Checks if it's Friday or a Birthday
    @tasks.loop(seconds=60)
    async def check_time(self):
        """Sends a good morning happy friday gif at a certain time"""
        main_channel = self.bot.config.main_channel
        now = dt.datetime.now()
        
        # Automated messages will be sent at noon
        if now.hour == 12 and now.minute == 00:
            # Checks to see if it's Friday
            if now.weekday() == 4:
                await main_channel.send("https://tenor.com/view/happy-friday-good-morning-friday-morning-gif-13497103")
            
            # Checks to see if it's anyone's birthday
            date = now.strftime("%m/%d/%Y")
            
            for user_id, birthday in self.birthdays.items():
                if date == birthday:
                    user = self.bot.get_user(user_id)
                    await main_channel.send(
                         f"{user.mention} https://tenor.com/view/holiday-classics-elf-christmas-excited-happy-gif-15741376"
                    )

def setup(bot:toof.ToofBot):
    bot.add_cog(ToofCommands(bot))
    bot.add_cog(ToofEvents(bot))
