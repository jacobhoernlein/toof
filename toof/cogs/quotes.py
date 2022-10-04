"""Extension that allows users to quote messages or things that people
say in voice chat either by command or context menu. They then get
added to the quoteboard channel.
"""

import discord

from .. import base


class QuotesCog(base.Cog):
    """Cog containing a quote context menu and command."""

    async def cog_load(self):
        self.bot.tree.add_command(
            discord.app_commands.ContextMenu(
                name="Quote Message",
                callback=self.quote_context_callback))

    async def get_quotes_channel(
            self,
            guild: discord.Guild) -> discord.TextChannel | None:
        """Get the quotes channel of the guild by searching the database."""
        
        query = f"SELECT quotes_channel_id FROM guilds WHERE guild_id = {guild.id}"
        async with self.bot.db.execute(query) as cursor:
            row = await cursor.fetchone()

        return None if row is None else discord.utils.find(
            lambda c: c.id == row[0],
            guild.channels)

    @discord.app_commands.guild_only()
    async def quote_context_callback(
            self, interaction: discord.Interaction,
            msg: discord.Message):
        """Allows users to add quotes to the quoteboard by using a
        context menu
        """
        
        if msg.content:
            embed = discord.Embed(
                description=msg.content,
                color=discord.Color.blurple(),
                timestamp=msg.created_at)
        else:
            embed = discord.Embed(
                color=discord.Colour.blurple(),
                timestamp=msg.created_at)
        if msg.attachments:
            attachment_url = msg.attachments[0].url
            embed.set_image(url=attachment_url)
        embed.set_author(
            name=f"{msg.author}:",
            icon_url=msg.author.avatar.url)

        quotes_channel = await self.get_quotes_channel(interaction.guild)

        if quotes_channel is None:
            await interaction.response.send_message(
                content="ruh roh. culdnt send quorte...",
                ephemeral=True)
        else:
            await quotes_channel.send(
                content=f"Quote submitted by {interaction.user.mention}:",
                embed=embed,
                view=discord.ui.View().add_item(
                    discord.ui.Button(
                        style=discord.ButtonStyle.link,
                        label="Jump To Message",
                        url=msg.jump_url,
                        emoji="⤴️")))
            await interaction.response.send_message(
                content="quote sent 😎",
                ephemeral=True)

    @discord.app_commands.command(
        name="quote",
        description="Add a quote to the quoteboard.")
    @discord.app_commands.guild_only()
    @discord.app_commands.describe(
        member="The member to quote.",
        quote="What they said.")
    async def quote_command(
            self, interaction: discord.Interaction,
            member: discord.Member, quote: str):
        """Command to add a quote to the quoteboard."""
        
        embed = discord.Embed(
            description=quote,
            color=discord.Color.blurple(),
            timestamp=interaction.created_at)
        embed.set_author(
            name=f"{member}:",
            icon_url=member.avatar.url)
  
        quotes_channel = await self.get_quotes_channel(interaction.guild)

        if quotes_channel is None:
            await interaction.response.send_message(
                content="ruh roh. culdnt send quorte...",
                ephemeral=True)
        else:
            await quotes_channel.send(
                content=f"Quote submitted by {interaction.user.mention}:",
                embed=embed)
            await interaction.response.send_message(
                content="quote sent 😎",
                ephemeral=True)
