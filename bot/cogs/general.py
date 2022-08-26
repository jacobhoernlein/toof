"""Basic commands for Toof"""

import json
import datetime as dt
from random import choice

import discord
from discord.ext import commands, tasks

import toof


class ToofEvents(commands.Cog):
    """Cog that contains basic event handling"""

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.change_status.start()
        self.check_time.start()

    def cog_unload(self):
        self.change_status.cancel()
        self.check_time.cancel()

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
        
        with open('configs/birthdays.json') as fp:
            birthdays:dict = json.load(fp)

        # Automated messages will be sent at noon
        if now.hour == 12 and now.minute == 00:
            # Checks to see if it's Friday
            if now.weekday() == 4:
                await main_channel.send("https://tenor.com/view/happy-friday-good-morning-friday-morning-gif-13497103")
            
            # Checks to see if it's anyone's birthday
            date = now.strftime("%m/%d/%Y")
            
            for user_id, birthday in birthdays.items():
                if date == birthday:
                    user = self.bot.get_user(user_id)
                    await main_channel.send(
                         f"{user.mention} https://tenor.com/view/holiday-classics-elf-christmas-excited-happy-gif-15741376"
                    )

    @commands.Cog.listener()
    async def on_member_join(self, member:discord.Member):
        """Sends a message to the welcome channel when a new member joins"""
        await member.add_roles(self.bot.config.member_role)

    # Replies to messages that have certain phrases in them    
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        """Listens for specific messages"""

        # Ignores messages sent by the bot and messages sent in the welcome channel
        if msg.author == self.bot.user or msg.channel == self.bot.config.welcome_channel:
            return
        
        # Logs DMs
        if isinstance(msg.channel, discord.DMChannel):
            dm_channel = self.bot.get_channel(1006036934075891732)

            files = []
            if msg.attachments:
                for attachment in msg.attachments:
                    files.append(await attachment.to_file())
                
            await dm_channel.send(
                f"{str(msg.author)}: {msg.content}",
                files=files
            )

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
            if msg.reference.cached_message.author.bot:
                return
            emoji = discord.utils.find(lambda e : e.name == 'toofping', msg.guild.emojis)
            if emoji:
                await msg.add_reaction(emoji)
            else:
                await msg.add_reaction("🇵")
                await msg.add_reaction("🇮")
                await msg.add_reaction("🇳")
                await msg.add_reaction("🇬")            
                    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction:discord.Reaction, usr:discord.User):
        if reaction.message.mentions and reaction.message.reference:
            referenced_message = reaction.message.reference.cached_message
            if referenced_message.author == usr \
            and reaction.emoji.name == 'toofping' \
            and self.bot.user in [member async for member in reaction.users()]:
                await reaction.message.reply(f"https://tenor.com/view/discord-reply-discord-reply-off-discord-reply-gif-22150762")
                await reaction.message.remove_reaction(reaction.emoji, self.bot.user)


async def setup(bot:toof.ToofBot):
    await bot.add_cog(ToofEvents(bot))

    @bot.tree.command(name="speak", description="Check Toof's latency.")
    async def speak(interaction:discord.Interaction):
        await interaction.response.send_message(f"woof! ({round(bot.latency * 1000)}ms)", ephemeral=True)

    # Allows users to add quotes to the quoteboard by using a context menu
    @bot.tree.context_menu(name="Quote Message")
    @discord.app_commands.guild_only()
    async def quote_context(interaction:discord.Interaction, msg:discord.Message):
        if msg.content:
            embed = discord.Embed(
                description=msg.content,
                color=discord.Color.blurple()
            )
        else:
            embed = discord.Embed(colour=discord.Colour.blurple())
        if msg.attachments:
            attachment_url = msg.attachments[0].url
            embed.set_image(url=attachment_url)

        embed.set_author(
            name=f"{msg.author.name}#{msg.author.discriminator} (click to jump):",
            url=msg.jump_url,
            icon_url=msg.author.avatar.url
        )

        date = msg.created_at.strftime("%m/%d/%Y")
        embed.set_footer(text=date)

        await bot.config.quotes_channel.send(
            content=f"{interaction.user.mention} submitted a quote:",
            embed=embed 
        )
        await interaction.response.send_message("✅", ephemeral=True)

    # Command to add a quote to the quoteboard.
    @bot.tree.command(
        name="quote",
        description="Add a quote to the quoteboard."
    )
    @discord.app_commands.guild_only()
    @discord.app_commands.describe(
        member="The member to quote.",
        quote="What they said."
    )
    async def quote_command(interaction:discord.Interaction, member:discord.Member, quote:str):
        embed = discord.Embed(
            description=quote,
            color=discord.Color.blurple()
        )

        embed.set_author(
            name=f"{member.name}#{member.discriminator}:",
            icon_url=member.avatar.url
        )
        
        if interaction.message and interaction.message.attachments:
            attachment_url = interaction.message.attachments[0].url
            embed.set_image(url=attachment_url)
        
        date = dt.datetime.now().strftime("%m/%d/%Y")
        embed.set_footer(text=date)

        await bot.config.quotes_channel.send(
            content=f"{interaction.user.mention} submitted a quote:",
            embed=embed 
        )
        await interaction.response.send_message("✅", ephemeral=True)

    with open('configs/birthdays.json') as fp:
        birthdays:dict = json.load(fp)

    @bot.tree.context_menu(name="Birthday")
    async def birthday_context(interaction:discord.Interaction, member:discord.Member):
        for user_id, birthday in birthdays.items():
            if str(member.id) == str(user_id):
                await interaction.response.send_message(f"woof! ({birthday})", ephemeral=True)
                return

        await interaction.response.send_message("...", ephemeral=True)
        
    @bot.tree.command(name="birthday", description="Tell Toof your birthday.")
    @discord.app_commands.describe(birthday="Format as mm/dd/yyyy.")
    async def birthday_update(interaction:discord.Interaction, birthday:str):
        try:
            day = dt.datetime.strptime(birthday, "%m/%d/%Y")
        # Formatting went wrong
        except ValueError:
            await interaction.response.send_message("woof! (mm/dd/yyyy)", ephemeral=True)
            return

        # Converts day from datetime object to string, stores in library
        day = day.strftime("%m/%d/%Y")
        birthdays[str(interaction.user.id)] = day

        with open("configs/birthdays.json", "w") as fp:
            json.dump(birthdays, fp, indent=4)

        await interaction.response.send_message("✅", ephemeral=True)
          