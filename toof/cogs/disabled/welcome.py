"""Extension that sends a message and creates a thread when someone
joins the server. They will have access to the thread but not the rest
of the server.
"""

import discord
from discord.ext.commands import Cog

import toof


class WelcomeChannelConfig(discord.app_commands.Group):

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="welcome",
            description="Change settings dealing with the Welcome Channel.")
        self.bot = bot

    @discord.app_commands.command(
        name="disable",
        description="Disable the Welcome Channel.")
    async def disable_command(self, interaction: discord.Interaction):
        query = f"""
            UPDATE guilds
            SET welcome_channel_id = 0
            WHERE guild_id = {interaction.guild_id}"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            "Welcome Channel disabled.", ephemeral=True)

    @discord.app_commands.command(
        name="set",
        description="Set the Welcome Channel to the current channel.")
    async def set_command(self, interaction: discord.Interaction):
        query = f"""
            UPDATE guilds
            SET welcome_channel_id = {interaction.channel_id}
            WHERE guild_id = {interaction.guild_id}"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            f"Welcome Channel set to {interaction.channel.mention}",
            ephemeral=True)


class WelcomeCommandGroup(discord.app_commands.Group):

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="welcome",
            description="Commands relating to welcome threads.",
            guild_only=True)
        self.bot = bot

    @discord.app_commands.command(
        name="approve",
        description="Approve the user..")
    async def approve_command(self, interaction: discord.Interaction):
        """Adds the member role to the user and locks the guild."""

        member = await self.get_thread_member(interaction.channel)
        role = await self.bot.get_member_role(interaction.guild)

        if member is None:
            await interaction.response.send_message(
                "u gotta do this in a welcom thred!",
                ephemeral=True)
            return
        if role is None:
            await interaction.response.send_message(
                "ur member role isnt set up right !!",
                ephemeral=True)
            return
        
        await interaction.response.send_message(
            f"{member.mention} haz been accepted 😎")
        await member.add_roles(role)
        await interaction.channel.edit(archived=True, locked=True)
        await self.remove_thread(interaction.channel)

    @discord.app_commands.command(
        name="deny",
        description="Deny this user.")
    async def deny_command(self, interaction: discord.Interaction):
        
        member = await self.get_thread_member(interaction.channel)

        if member is None:
            await interaction.response.send_message(
                "u gotta do this in a welcom thred!",
                ephemeral=True)
            return

        await interaction.response.send_message(
            f"{member} haz been rejected 👢")
        await member.kick()
        await interaction.channel.edit(archived=True, locked=True)
        await self.remove_thread(interaction.channel)

    async def get_thread_member(self, thread: discord.Thread):
        """Get the member that the thread maps to by searching the
        database.
        """

        query = f"""
            SELECT user_id
            FROM threads
            WHERE thread_id = {thread.id}"""
        async with self.bot.db.execute(query) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        
        return discord.utils.find(
            lambda m: m.id == row[0],
            thread.guild.members)

    async def remove_thread(self, thread: discord.Thread):
        """Remove the thread from the database."""
        
        query = f"""
            DELETE FROM threads
            WHERE thread_id = {thread.id}"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()


class WelcomeCog(Cog):

    def __init__(self, bot: toof.ToofBot):
        bot.tree.add_command(WelcomeCommandGroup(bot))
        self.bot = bot

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Creates a new thread whenever a member joins the guild."""
        
        mod_role = await self.bot.get_mod_role(member.guild)
        welcome_channel = await self.bot.get_welcome_channel(member.guild)

        if welcome_channel is None or mod_role is None:
            return

        if member.guild.premium_tier > 1:
            welcome_thread = await welcome_channel.create_thread(
                name=f"{member}'s interrogation",
                invitable=False)
            await welcome_thread.send(
                f"welcum {member.mention}. pls wait here. a {mod_role.mention} wil b here soon 👍")
        else:
            welcome_message = await welcome_channel.send(
                f"welcum {member.mention} to {member.guild.name}!")
            welcome_thread = await welcome_message.create_thread(
                name=f"{member}'s welcome thread")

        query = f"""
            INSERT INTO threads
            VALUES (
                {welcome_thread.id},
                {member.id})"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()


async def setup(bot: toof.ToofBot):
    await bot.add_cog(WelcomeCog(bot))
    