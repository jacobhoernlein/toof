"""Moderation commands and features"""

import asyncio

import discord
from discord.ext import commands

import toof


def has_mod_perms(mbr:discord.Member, mod_role:discord.Role) -> bool:
    """Makes sure the given member has the given mod_role or is admin"""
    if mod_role in mbr.roles or mbr.guild_permissions.administrator:
        return True
    return False

def convert_time(duration:float, unit:str) -> int:
    """Converts a duration and a unit to seconds"""

    seconds = ["seconds", "second", "secs", "sec", "s"]
    minutes = ["minutes", "minute", "mins", "min", "m"]
    hours = ["hours", "hour", "h"]
       
    if unit in seconds:
        multiplier = 1
    if unit in minutes:
        multiplier = 60
    if unit in hours:
        multiplier = 3600

    return round(duration * multiplier)


class ToofMod(commands.Cog):
    """Commands that implement moderation functionality"""

    def __init__(self, bot:toof.ToofBot):
        self.bot = bot

        self.log_channel:discord.TextChannel = lambda ctx : discord.utils.find(
            lambda c : c.id == self.bot.serverconf['channels']['log'],
            ctx.guild.channels
        )

        self.mod_role:discord.Role = lambda ctx : discord.utils.find(
            lambda r : r.id == self.bot.serverconf['roles']['mod'],
            ctx.guild.roles
        )

        self.mute_role:discord.Role = lambda ctx : discord.utils.find(
            lambda r : r.id == self.bot.serverconf['roles']['mute'],
            ctx.guild.roles
        )

        self.member_role:discord.Role = lambda ctx : discord.utils.find(
            lambda r : r.id == self.bot.serverconf['roles']['member'],
            ctx.guild.roles
        )

    ### UTILITY METHODS ###

    # Finds the mod role for the server based on the context
    def get_mod_role(self, ctx:commands.Context) -> discord.Role:
        """Gets the mod role based on the config file"""
        role = discord.utils.find(lambda r: r.id == self.bot.serverconf["roles"]["mod"], ctx.guild.roles)
        return role

    # Finds the mute role for the server based on the context
    def get_mute_role(self, ctx:commands.Context) -> discord.Role:
        """Gets the mute role based on the config file"""
        role = discord.utils.find(lambda r: r.id == self.bot.serverconf["roles"]["mute"], ctx.guild.roles)
        return role

    # Adds reactions to a message based on a given time in seconds
    async def add_time_reactions(self, msg:discord.Message, seconds:int):
        """Adds reactions to a message based on the time input in seconds"""
        emoji = [
            '0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣',
            '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'
        ]
        
        hours = seconds // 3600
        seconds -= hours * 3600
        minutes = seconds // 60
        seconds -= minutes * 60

        if hours != 0:
            hours_digits = []

            while hours != 0:
                digit = hours % 10
                hours = hours // 10
                hours_digits.insert(0, digit)

            for digit in hours_digits:
                await msg.add_reaction(emoji[digit])
            
            await msg.add_reaction('🇭')
    
        if minutes != 0:
            minute_digits = []

            while minutes != 0:
                digit = minutes % 10
                minutes = minutes // 10
                minute_digits.insert(0, digit)

            for digit in minute_digits:
                await msg.add_reaction(emoji[digit])

            await msg.add_reaction('🇲')

        if seconds != 0:
            second_digits = []

            while seconds != 0:
                digit = seconds % 10
                seconds = seconds // 10
                second_digits.insert(0, digit)

            for digit in second_digits:
                await msg.add_reaction(emoji[digit])

            await msg.add_reaction('🇸')

    # Logs the command in the proper channel
    async def log_command(self, ctx:commands.Context, target:discord.Member, time:float=None, unit:str=None, reason:str=None):
        """Logs the command in the log channel"""
        command_name = ctx.command.qualified_name

        if command_name == 'mute':
            embed = discord.Embed(
                description=f"Muted {target.mention} for {time} {unit}.",
                color=discord.Color.red()
            )
        elif command_name =='unmute':
            embed = discord.Embed(
                description=f"Unmuted {target.mention}.",
                color=discord.Color.green()
            )
        elif command_name == 'kick':
            embed = discord.Embed(
                description=f"Kicked {target.mention} for reason: \"{reason}\".",
                color=discord.Color.red()
            )
        elif command_name == 'ban':
            embed = discord.Embed(
                description=f"Banned {target.mention} for reason: \"{reason}\".",
                color=discord.Color.red()
            )
        elif command_name == 'unban':
            embed = discord.Embed(
                description=f"Unbanned {target.mention}.",
                color=discord.Color.red()
            )

        embed.set_author(
            name=f"{ctx.author.name}#{ctx.author.discriminator} (Click to Jump):",
            url=ctx.message.jump_url,
            icon_url=ctx.author.avatar_url
        )

        date = ctx.message.created_at.strftime("%m/%d/%Y %H:%M")
        embed.set_footer(
            text=f"Message ID: {ctx.message.id} - {date} UTC"
        )

        await self.log_channel(ctx).send(
            embed=embed
        )

    ### COMMANDS ###

    # Mutes the target user for the specified duration
    @commands.command()
    async def mute(self, ctx:commands.Context, target:discord.Member, time:float=5, unit:str="minutes"):
        """Mutes a member"""
        mod_role = self.mod_role(ctx)
        mute_role = self.mute_role(ctx)
        seconds = convert_time(time, unit.lower())

        if not has_mod_perms(ctx.author, mod_role):
            await ctx.message.add_reaction("❌")
            return

        if mute_role not in target.roles:
            await target.add_roles(mute_role)
            await ctx.message.add_reaction("👍")
            await self.log_command(ctx, target, time, unit)
            await self.add_time_reactions(ctx.message, seconds)
        
            await asyncio.sleep(seconds)
            if mute_role in target.roles:
                await target.remove_roles(mute_role)

    # Unmutes the target user if they are muted
    @commands.command()
    async def unmute(self, ctx:commands.Context, target:discord.Member):
        """Unmutes a member"""
        mod_role = self.mod_role(ctx)
        mute_role = self.mute_role(ctx)
        
        if not has_mod_perms(ctx.author, mod_role):
            await ctx.message.add_reaction("❌")
            return

        if mute_role in target.roles:
            await target.remove_roles(mute_role)
            await ctx.message.add_reaction("👍")
            await self.log_command(ctx, target)

    # Kicks that target user for the specified reason
    @commands.command()
    async def kick(self, ctx:commands.Context, target:discord.Member, *, reason:str=None):
        """Kicks a member from the server"""
        mod_role = self.mod_role(ctx)
        
        if not has_mod_perms(ctx.author, mod_role):
            await ctx.message.add_reaction("❌")
            return

        await target.kick(reason=reason)
        await ctx.message.add_reaction("👍")
        await self.log_command(ctx, target, reason=reason)
        
    # Bans the target user for the specified reason
    @commands.command()
    async def ban(self, ctx:commands.Context, target:discord.Member, *, reason:str=None):
        """Bans a member from the server"""
        mod_role = self.mod_role(ctx)
        
        if not has_mod_perms(ctx.author, mod_role):
            await ctx.message.add_reaction("❌")
            return

        await target.ban(reason=reason, delete_message_days=0)
        await ctx.message.add_reaction("👍")
        await self.log_command(ctx, target, reason=reason)
        
    # Unbans the user if the user is banned
    @commands.command()
    async def unban(self, ctx:commands.Context, target:discord.Member):
        """Unbans a member from the server"""
        mod_role = self.mod_role()

        if not has_mod_perms(ctx.author, mod_role):
            await ctx.message.add_reaction("❌")
            return

        await target.unban()
        await ctx.message.add_reaction("👍")
        await self.log_command(ctx, target)
    
    ### EVENTS ###

    # Verifies users if they say "woof" in the welcome channel. Deletes the message.
    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        """Verifies users"""
        if message.author == self.bot.user or message.author.id == 243845903146811393:
            return

        member_role = self.member_role(message)
        
        if message.channel.id == self.bot.serverconf['channels']['welcome']:
            if message.content == 'woof' and member_role not in message.author.roles:
                await message.author.add_roles(member_role)
            await message.delete()

    # Snipes deleted messages and puts them into the mod log
    @commands.Cog.listener()
    async def on_message_delete(self, message:discord.Message):
        """Logs deleted messages"""
        if message.channel.id == self.bot.serverconf['channels']['welcome']:
            return

        if message.author.id == self.bot.user.id:
            return

        embed = discord.Embed(
            description=message.content,
            color=discord.Color.red()
        )

        embed.set_author(
            name=f"Message sent by {message.author.name}#{message.author.discriminator} deleted in #{message.channel.name}:",
            icon_url=message.author.avatar_url
        )

        if message.attachments:
            attachment_url = message.attachments[0].url
            embed.set_image(url=attachment_url)

        date = message.created_at.strftime("%m/%d/%Y %H:%M")
        embed.set_footer(
            text=f"Message ID: {message.id} - {date} UTC"
        )

        await self.log_channel(message).send(
            embed=embed
        )

    # Watches for messages being edited
    @commands.Cog.listener()
    async def on_message_edit(self, before:discord.Message, after:discord.Message):
        """Watches for messages that are edited"""

        # We only care about the content of the messages being changed
        if before.content == after.content:
            return

        embed = discord.Embed(
            color=discord.Color.blurple()
        )

        embed.set_author(
            name=f"Message sent by {before.author.name}#{before.author.discriminator} edited in #{before.channel.name} (Click to Jump):",
            url=before.jump_url,
            icon_url=before.author.avatar_url
        )

        embed.add_field(
            name="Before:",
            value=before.content
        )
        embed.add_field(
            name="After:",
            value=after.content
        )

        date = after.edited_at.strftime("%m/%d/%Y %H:%M")
        embed.set_footer(
            text=f"Message ID: {after.id} - {date} UTC"
        )

        await self.log_channel(before).send(embed=embed)


def setup(bot:toof.ToofBot):
    bot.add_cog(ToofMod(bot))
