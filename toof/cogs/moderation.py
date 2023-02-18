"""Extension which contains the moderation cog, which allows the bot to
listen for deleted and edited messages, as well as accept modmails and
kicks people for listening to Doja Cat (real).
"""

import discord
from discord.ext.commands import Cog

import toof


class ModLogConfig(discord.app_commands.Group):
    """Config for setting the Mod Log."""

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="log",
            description="Change settings dealing with the Mod Log.")
        self.bot = bot

    @discord.app_commands.command(
        name="disable",
        description="Disable the Mod Log.")
    async def disable_command(self, interaction: discord.Interaction):
        query = f"""
            UPDATE guilds
            SET log_channel_id = 0
            WHERE guild_id = {interaction.guild_id}"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            "Mod Log disabled.", ephemeral=True)

    @discord.app_commands.command(
        name="set",
        description="Set the Log Channel to the current channel.")
    async def set_command(self, interaction: discord.Interaction):
        query = f"""
            UPDATE guilds
            SET log_channel_id = {interaction.channel_id}
            WHERE guild_id = {interaction.guild_id}"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            f"Mod Log set to {interaction.channel.mention}",
            ephemeral=True)


class ModmailModal(discord.ui.Modal):
    """Modal to be sent to users running the Modmail command"""

    def __init__(self, bot: toof.ToofBot):
        super().__init__(title="New Modmail")
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

        log_channel = await self.bot.get_log_channel(interaction.guild)
        mod_role = await self.bot.get_mod_role(interaction.guild)

        if log_channel is None or mod_role is None:
            await interaction.response.send_message(
                content="modmail culdnt b send :(",
                ephemeral=True)
        else:
            embed = discord.Embed(
                color=discord.Color.blue(),
                description=self.details.value,
                timestamp=interaction.created_at)
            embed.set_author(name=f"RE: {self.subject.value}")
            embed.set_footer(
                text=f"From {interaction.user}", 
                icon_url=interaction.user.avatar.url)
            
            await log_channel.send(
                content=f"{mod_role.mention} New Modmail:",
                embed=embed)
            await interaction.response.send_message(
                content="modmail sent.:)",
                ephemeral=True)


class ModmailCommand(discord.app_commands.Command):
    """Sends the modmail modal to the user."""

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="modmail",
            description="Something bothering you? Tell the mods.",
            callback=self.callback)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ModmailModal(self.bot))


class ModCog(Cog):

    def __init__(self, bot: toof.ToofBot):
        bot.tree.add_command(ModmailCommand(bot))
        self.bot = bot

    @Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        log_channel = await self.bot.get_log_channel(message.guild)
        if log_channel is None or message.channel == log_channel:
            return
        
        if message.channel.id == 937093915482415104: # temp fix (no thanks)
            return

        embed = discord.Embed(
            description=message.content,
            color=discord.Color.red(),
            timestamp=message.created_at)
        embed.set_author(
            name=f"Message sent by {message.author} deleted in #{message.channel}:",
            icon_url=message.author.avatar.url)
        embed.set_footer(text=f"Message ID: {message.id}")
        
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        
        await log_channel.send(embed=embed)

    @Cog.listener()
    async def on_message_edit(
            self, before: discord.Message,
            after: discord.Message):
        if before.author.bot or before.content == after.content:
            return

        log_channel = await self.bot.get_log_channel(before.guild)
        if log_channel is None or before.channel == log_channel:
            return

        embed = discord.Embed(
            color=discord.Color.orange(),
            timestamp=after.edited_at)
        embed.set_author(
            name=f"Message sent by {before.author} edited in #{before.channel}:",
            icon_url=before.author.avatar.url)
        embed.add_field(name="Before:", value=before.content)
        embed.add_field(name="After:", value=after.content)
        embed.set_footer(text=f"Message ID: {after.id}")
  
        await log_channel.send(
            embed=embed,
            view=discord.ui.View().add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    label="Jump To Message",
                    url=before.jump_url,
                    emoji="⤴️")))

    @Cog.listener()
    async def on_presence_update(
            self, before: discord.Member, 
            after: discord.Member):
        for activity in after.activities:
            if (isinstance(activity, discord.Spotify)
                and activity.title == "Say So"
                and activity.artist == "Doja Cat"):
                
                    reason = "Listening to Say So by Doja Cat"
                    await after.send(f"u were kickd 4 \"{reason}\" :(")
                    await after.kick(reason=reason)

                    break
                    
    
async def setup(bot: toof.ToofBot):
    await bot.add_cog(ModCog(bot))
    