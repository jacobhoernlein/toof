"""Moderation commands and features"""

import discord
from discord.ext import commands

import toof


class ToofMod(commands.Cog):
    """Events that implement moderation functionality"""

    def __init__(self, bot:toof.ToofBot):
        self.bot = bot
      
    # Snipes deleted messages and puts them into the mod log
    @commands.Cog.listener()
    async def on_message_delete(self, message:discord.Message):
        if message.author.bot \
        or message.channel == self.bot.config.log_channel:
            return
        
        embed = discord.Embed(
            description=message.content,
            color=discord.Color.red()
        )

        embed.set_author(
            name=f"Message sent by {message.author.name}#{message.author.discriminator} deleted in #{message.channel.name}:",
            icon_url=message.author.avatar.url
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
        if before.author.bot:
            return

        # We only care about the content of the messages being changed
        if before.content == after.content:
            return

        embed = discord.Embed(
            color=discord.Color.blurple()
        )

        embed.set_author(
            name=f"Message sent by {before.author.name}#{before.author.discriminator} edited in #{before.channel.name} (Click to Jump):",
            url=before.jump_url,
            icon_url=before.author.avatar.url
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
    async def on_presence_update(self, before:discord.Member, after:discord.Member):
        for activity in after.activities:
            if isinstance(activity, discord.Spotify):
                if activity.title == "Say So" and activity.artist == "Doja Cat":
                    reason = "Listening to Say So by Doja Cat"
                    await after.send(f"You were kicked for {reason}")
                    await after.kick(reason=reason)
                    

async def setup(bot:toof.ToofBot):
    await bot.add_cog(ToofMod(bot))
    