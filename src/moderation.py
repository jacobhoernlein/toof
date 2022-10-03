"""Extension which contains the moderation cog, which allows the bot to
listen for deleted and edited messages, as well as accept modmails and
kick people for listening to Doja Cat (real).
"""

import discord
from discord.ext import commands

import toof


class ModmailModal(discord.ui.Modal):
    """Modal to be sent to users running the Modmail command"""

    def __init__(self, bot: toof.ToofBot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.bot = bot

    subject = discord.ui.TextInput(
        label="Subject",
        style=discord.TextStyle.short,
        placeholder="A short summary of what's wrong.",
        max_length=50)
    details = discord.ui.TextInput(
        label="Details",
        style=discord.TextStyle.long,
        placeholder="Give us more details on what exactly happened.")

    async def on_submit(self, interaction: discord.Interaction):
        """Summarizes the modal data and sends it to the log channel of
        the guild.
        """

        embed = discord.Embed(
            color=discord.Color.blue(),
            description=self.details.value,
            timestamp=interaction.created_at)
        embed.set_author(name=f"RE: {self.subject.value}")
        embed.set_footer(
            text=f"From {interaction.user}", 
            icon_url=interaction.user.avatar.url)

        query = f"SELECT log_channel_id, mod_role_id FROM guilds WHERE guild_id = {interaction.guild_id}"
        async with self.bot.db.execute(query) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return

        log_channel = discord.utils.find(
            lambda c: c.id == row[0],
            interaction.guild.channels)
        mod_role = discord.utils.find(
            lambda r: r.id == row[1],
            interaction.guild.roles)

        if log_channel is None or mod_role is None:
            await interaction.response.send_message(
                content="modmail culdnt b send :(",
                ephemeral=True)
        else:
            await log_channel.send(
                content=f"{mod_role.mention} New Modmail:",
                embed=embed)
            await interaction.response.send_message(
                content="modmail sent.:)",
                ephemeral=True)


class ModCog(commands.Cog):
    """Cog containing listeners for message editing/deleting
    as well as status updates.
    """

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
      
    async def get_log_channel(
            self,
            guild: discord.Guild) -> discord.TextChannel | None:
        """Get the guild's log_channel by searching the database."""

        query = f"SELECT log_channel_id FROM guilds WHERE guild_id = {guild.id}"
        async with self.bot.db.execute(query) as cursor:
            row = await cursor.fetchone()

        return None if row is None else discord.utils.find(
            lambda c: c.id == row[0],
            guild.channels)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Snipes deleted messages and puts them into the server's mod
        log.
        """
        
        if message.author.bot:
            return

        log_channel = await self.get_log_channel(message.guild)
        if log_channel is None or message.channel == log_channel:
            return
        
        embed = discord.Embed(
            description=message.content,
            color=discord.Color.red(),
            timestamp=message.created_at)
        embed.set_author(
            name=f"Message sent by {message.author} deleted in #{message.channel}:",
            icon_url=message.author.avatar.url)
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        embed.set_footer(
            text=f"Message ID: {message.id}")

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(
            self, before: discord.Message,
            after: discord.Message):
        """Watches for messages being edited and puts a summary in the
        server's log channel.
        """
    
        if before.author.bot or before.content == after.content:
            return

        log_channel = await self.get_log_channel(before.guild)
        if log_channel is None:
            return

        embed = discord.Embed(
            color=discord.Color.orange(),
            timestamp=after.edited_at)
        embed.set_author(
            name=f"Message sent by {before.author} edited in #{before.channel}:",
            icon_url=before.author.avatar.url)
        embed.add_field(
            name="Before:",
            value=before.content)
        embed.add_field(
            name="After:",
            value=after.content)
        embed.set_footer(
            text=f"Message ID: {after.id}")
  
        await log_channel.send(
            embed=embed,
            view=discord.ui.View().add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    label="Jump To Message",
                    url=before.jump_url,
                    emoji="⤴️")))

    @commands.Cog.listener()
    async def on_presence_update(
            self, before: discord.Member, 
            after: discord.Member):
        """Kicks people for listening to Say So by Doja Cat"""
        
        for activity in after.activities:
            if (isinstance(activity, discord.Spotify)
                and activity.title == "Say So"
                and activity.artist == "Doja Cat"):
                
                    reason = "Listening to Say So by Doja Cat"
                    await after.send(f"u were kickd 4 \"{reason}\" :(")
                    await after.kick(reason=reason)

                    break
                    
    @discord.app_commands.command(
        name="modmail",
        description="Something bothering you? Tell the mods.")
    async def modmail_command(self, interaction: discord.Interaction):
        """Sends the modmail modal to the user."""
        
        await interaction.response.send_modal(
            ModmailModal(self.bot, title="New Modmail"))


async def setup(bot: toof.ToofBot):
    await bot.add_cog(ModCog(bot))
    