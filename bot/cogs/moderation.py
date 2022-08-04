"""Moderation commands and features"""

import asyncio
import datetime as dt

import discord
from discord.ext import commands

import toof

class ToofMod(commands.Cog):
    """Commands that implement moderation functionality"""

    def __init__(self, bot:toof.ToofBot):
        self.bot = bot

    ### UTILITY METHODS ###

    # Adds reactions to a message based on a given time in seconds
    async def add_time_reactions(self, msg:discord.Message, seconds:int):
        """Adds reactions to a message based on the time input in seconds"""
        emoji = [
            '0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣',
            '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'
        ]
        
        hours = int(seconds / 3600)
        seconds = int(seconds - (hours * 3600))
        minutes = int(seconds / 60)
        seconds = int(seconds - (minutes * 60))

        if hours != 0:
            hours_digits = []

            while hours != 0:
                digit = int(hours % 10)
                hours = int(hours / 10)
                hours_digits.insert(0, digit)

            for digit in hours_digits:
                await msg.add_reaction(emoji[digit])
            
            await msg.add_reaction('🇭')
    
        if minutes != 0:
            minute_digits = []

            while minutes != 0:
                digit = int(minutes % 10)
                minutes = int(minutes / 10)
                minute_digits.insert(0, digit)

            for digit in minute_digits:
                await msg.add_reaction(emoji[digit])

            await msg.add_reaction('🇲')

        if seconds != 0:
            second_digits = []

            while seconds != 0:
                digit = int(seconds % 10)
                seconds = int(seconds / 10)
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

        await self.bot.config.log_channel.send(
            embed=embed
        )

    ### COMMANDS ###

    # Mutes the target user for the specified duration
    @commands.command()
    async def mute(self, ctx:commands.Context, target:discord.Member, time:float=5, unit:str="minutes"):
        """Mutes a member"""
        if self.bot.config.mod_role in ctx.author.roles \
        or ctx.author.guild_permissions.administrator:
            mute_role = self.bot.config.mute_role
            
            if mute_role in target.roles:
                return

            seconds_aliases = ["seconds", "second", "secs", "sec", "s"]
            minutes_alises = ["minutes", "minute", "mins", "min", "m"]
            hours_aliases = ["hours", "hour", "h"]
            
            if unit in seconds_aliases:
                multiplier = 1
            elif unit in minutes_alises:
                multiplier = 60
            elif unit in hours_aliases:
                multiplier = 3600
            else:
                await ctx.message.add_reaction("❓")
                return

            seconds = time * multiplier

            await target.add_roles(mute_role)
            await ctx.message.add_reaction("👍")
            await self.log_command(ctx, target, time, unit)
            await self.add_time_reactions(ctx.message, seconds)
        
            await asyncio.sleep(seconds)
            if mute_role in target.roles:
                await target.remove_roles(mute_role)
        else:
            await ctx.message.add_reaction("❌")

    # Unmutes the target user if they are muted
    @commands.command()
    async def unmute(self, ctx:commands.Context, target:discord.Member):
        """Unmutes a member"""
        if self.bot.config.mod_role in ctx.author.roles \
        or ctx.author.guild_permissions.administrator:
            mute_role = self.bot.config.mute_role
            if mute_role in target.roles:
                await target.remove_roles(mute_role)
                await ctx.message.add_reaction("👍")
                await self.log_command(ctx, target)
        else:
            await ctx.message.add_reaction("❌")

    # Kicks that target user for the specified reason
    @commands.command()
    async def kick(self, ctx:commands.Context, target:discord.Member, *, reason:str=None):
        """Kicks a member from the server"""
        if self.bot.config.mod_role in ctx.author.roles \
        or ctx.author.guild_permissions.administrator:
            await target.kick(reason=reason)
            await ctx.message.add_reaction("👍")
            await self.log_command(ctx, target, reason=reason)
        else:
            await ctx.message.add_reaction("❌")
        
    # Bans the target user for the specified reason
    @commands.command()
    async def ban(self, ctx:commands.Context, target:discord.Member, *, reason:str=None):
        """Bans a member from the server"""
        if self.bot.config.mod_role in ctx.author.roles \
        or ctx.author.guild_permissions.administrator:
            await target.ban(reason=reason, delete_message_days=0)
            await ctx.message.add_reaction("👍")
            await self.log_command(ctx, target, reason=reason)
        else:
            await ctx.message.add_reaction("❌")
        
    # Unbans the user if the user is banned
    @commands.command()
    async def unban(self, ctx:commands.Context, target:discord.Member):
        """Unbans a member from the server"""
        if self.bot.config.mod_role in ctx.author.roles \
        or ctx.author.guild_permissions.administrator:
            await target.unban()
            await ctx.message.add_reaction("👍")
            await self.log_command(ctx, target)
        else:
            await ctx.message.add_reaction("❌")
    
    ### EVENTS ###

    # Verifies users if they say "woof" in the welcome channel. Deletes the message.
    # Only executes if the user has no roles.
    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        """Verifies users"""
        if message.channel == self.bot.config.welcome_channel \
        and len(message.author.roles) <= 1:
            
            await message.delete()
            member_role = self.bot.config.member_role
            
            if message.content == 'woof' and member_role not in message.author.roles:
                await message.author.add_roles(member_role)
            
    # Snipes deleted messages and puts them into the mod log
    @commands.Cog.listener()
    async def on_message_delete(self, message:discord.Message):
        """Logs deleted messages"""
        if message.author.id == self.bot.user.id \
        or message.channel == self.bot.config.log_channel \
        or (message.channel == self.bot.config.welcome_channel \
        and len(message.author.roles) <= 1):
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

        await self.bot.config.log_channel.send(
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

        await self.bot.config.log_channel.send(embed=embed)

    # Kicks people for listening to Say So by Doja Cat
    @commands.Cog.listener()
    async def on_member_update(self, before:discord.Member, after:discord.Member):
        for activity in after.activities:
            if isinstance(activity, discord.Spotify):
                if activity.title == "Say So" and activity.artist == "Doja Cat":
                    
                    reason = "Listening to Say So by Doja Cat"
                    await after.send(f"You were kicked for {reason}")
                    await after.kick(reason=reason)

                    embed = discord.Embed(
                        description=f"Kicked {after.mention} for reason: \"{reason}\".",
                        color=discord.Color.red()
                    )

                    embed.set_author(
                        name=f"{self.bot.user.name}#{self.bot.user.discriminator}:",
                        icon_url=self.bot.user.avatar_url
                    )

                    date = dt.datetime.now().strftime("%m/%d/%Y %H:%M")
                    embed.set_footer(
                        text=f"{date} UTC"
                    )

                    await self.bot.config.log_channel.send(
                        embed=embed
                    )
                    

def setup(bot:toof.ToofBot):
    bot.add_cog(ToofMod(bot))
