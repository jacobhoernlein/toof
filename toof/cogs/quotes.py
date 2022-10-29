"""Extension that allows users to quote messages or things that people
say in voice chat either by command or context menu. They then get
added to the quoteboard channel.
"""

import discord

import toof


class QuotesChannelConfig(discord.app_commands.Group):
    """Config for setting the voice channel."""

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="quotes",
            description="Change settings dealing with the Quotes Channel.")
        self.bot = bot

    @discord.app_commands.command(
        name="disable",
        description="Disable the Quotes Channel.")
    async def disable_command(self, interaction: discord.Interaction):
        query = f"""
            UPDATE guilds
            SET quotes_channel_id = 0
            WHERE guild_id = {interaction.guild_id}"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            "Quotes Channel disabled.", ephemeral=True)

    @discord.app_commands.command(
        name="set",
        description="Set the Quotes Channel to the current channel.")
    async def set_command(self, interaction: discord.Interaction):
        query = f"""
            UPDATE guilds
            SET quotes_channel_id = {interaction.channel_id}
            WHERE guild_id = {interaction.guild_id}"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            f"Quotes Channel set to {interaction.channel.mention}",
            ephemeral=True)


class QuoteContext(discord.app_commands.ContextMenu):
    """Allows users to add quotes to the quoteboard by using a context
    menu.
    """

    def __init__(self, bot: toof.ToofBot):
        super().__init__(name="Quote Message", callback=self.callback)
        self.guild_only = True
        self.bot = bot

    async def callback(
            self, interaction: discord.Interaction,
            message: discord.Message):
        
        embed = discord.Embed(
            description=message.content,
            color=discord.Colour.blurple(),
            timestamp=message.created_at
        ).set_author(
            name=f"{message.author}:",
            icon_url=message.author.avatar.url)
        if message.attachments:
            attachment_url = message.attachments[0].url
            embed.set_image(url=attachment_url)
        
        quotes_channel = await self.bot.get_quotes_channel(interaction.guild)

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
                        url=message.jump_url,
                        emoji="⤴️")))
            await interaction.response.send_message(
                content="quote sent 😎",
                ephemeral=True)


class QuoteCommand(discord.app_commands.Command):
    """Allows users to add quotes to the server's quoteboard via
    command.
    """

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="quote",
            description="Add a quote to the quoteboard.",
            callback=self.callback)
        self.guild_only = True
        self.bot = bot

    @discord.app_commands.describe(
        member="The member to quote.",
        quote="What they said.")
    async def callback(
            self, interaction: discord.Interaction,
            member: discord.Member, quote: str):
        
        embed = discord.Embed(
            description=quote,
            color=discord.Color.blurple(),
            timestamp=interaction.created_at
        ).set_author(
            name=f"{member}:",
            icon_url=member.avatar.url)
  
        quotes_channel = await self.bot.get_quotes_channel(interaction.guild)

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


async def setup(bot: toof.ToofBot):
    bot.tree.add_command(QuoteContext(bot))
    bot.tree.add_command(QuoteCommand(bot))
    