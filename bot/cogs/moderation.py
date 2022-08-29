"""Moderation commands and features"""

import discord
from discord.ext import commands

import toof


class ToofMod(commands.Cog):
    """Events that implement moderation functionality"""

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
      
    # Snipes deleted messages and puts them into the mod log
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot \
        or message.channel == self.bot.config.log_channel:
            return
        
        embed = discord.Embed(
            description=message.content,
            color=discord.Color.red(),
            timestamp=message.created_at
        )
        embed.set_author(
            name=f"Message sent by {message.author} deleted in #{message.channel}:",
            icon_url=message.author.avatar.url
        )
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        embed.set_footer(
            text=f"Message ID: {message.id}"
        )

        await self.bot.config.log_channel.send(
            embed=embed
        )

    # Watches for messages being edited
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content:
            return

        embed = discord.Embed(
            color=discord.Color.orange(),
            timestamp=after.edited_at
        )
        embed.set_author(
            name=f"Message sent by {before.author} edited in #{before.channel}:",
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
        embed.set_footer(
            text=f"Message ID: {after.id}"
        )

        await self.bot.config.log_channel.send(
            embed=embed,
            view=discord.ui.View().add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    label="Jump To Message",
                    url=before.jump_url,
                    emoji="⤴️"
                )
            )
        )

    # Kicks people for listening to Say So by Doja Cat
    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        for activity in after.activities:
            if isinstance(activity, discord.Spotify):
                if activity.title == "Say So" and activity.artist == "Doja Cat":
                    reason = "Listening to Say So by Doja Cat"
                    await after.send(f"You were kicked for {reason}")
                    await after.kick(reason=reason)
                    

class ModmailModal(discord.ui.Modal):
    """Modal to be sent to users running the Modmail command"""

    def __init__(self, bot: toof.ToofBot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    subject = discord.ui.TextInput(
        label="Subject",
        style=discord.TextStyle.short,
        placeholder="A short summary of what's wrong.",
        max_length=50
    )
    details = discord.ui.TextInput(
        label="Details",
        style=discord.TextStyle.long,
        placeholder="Give us more details on what exactly happened."
    )

    async def on_submit(self, interaction: discord.Interaction):
        
        embed = discord.Embed(
            color=discord.Color.blue(),
            description=self.details.value,
            timestamp=interaction.created_at
        )
        embed.set_author(name=f"RE: {self.subject.value}")
        embed.set_footer(
            text=f"From {interaction.user}", 
            icon_url=interaction.user.avatar.url
        )

        await self.bot.config.log_channel.send(embed=embed)
        await interaction.response.send_message(content="Modmail sent.", ephemeral=True)

async def setup(bot: toof.ToofBot):
    await bot.add_cog(ToofMod(bot))
    
    @bot.tree.command(name="modmail", description="Something bothering you? Tell the mods.")
    async def mod_mail(interaction: discord.Interaction):
        await interaction.response.send_modal(ModmailModal(bot, title="New Modmail"))
