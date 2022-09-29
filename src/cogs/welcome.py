"""
Extension that sends a message and creates a thread when someone
joins the server. They will have access to the thread but not the
rest of the server.
"""

import discord
from discord.ext import commands

import toof


class WelcomeCog(commands.Cog):
    """Cog that contains listeners for users joining the server"""

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
        self.threads: dict[discord.Thread, discord.Member] = {}

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        
        async with self.bot.db.execute(f'SELECT welcome_channel_id, mod_role_id FROM guilds WHERE guild_id = {member.guild.id}') as cursor:
            channel_mod_tuple = await cursor.fetchone()

        welcome_channel_id: int = channel_mod_tuple[0]
        mod_role_id: int = channel_mod_tuple[1]
        welcome_channel = discord.utils.find(lambda c: c.id == welcome_channel_id, member.guild.channels)
        mod_role = discord.utils.find(lambda r: r.id == mod_role_id, member.guild.roles)

        welcome_thread = await welcome_channel.create_thread(
            name=f"{member}'s interrogation",
            invitable=False
        )

        await welcome_thread.send(f"welcome {member.mention}. pls wait here. a {mod_role.mention} wil b here soon 👍")
        self.threads[welcome_thread] = member

    @discord.app_commands.command(name="accept", description="Approve the user to join the server.")
    @discord.app_commands.guild_only()
    async def accept_user(self, interaction: discord.Interaction):

        if interaction.channel not in self.threads.keys():
            await interaction.response.send_message("gotta do this in a welcum thred!", ephemeral=True)
            return
        
        thread: discord.Thread = interaction.channel
        member = self.threads[thread]

        async with self.bot.db.execute(f'SELECT member_role_id FROM guilds WHERE guild_id = {interaction.guild_id}') as cursor:
            member_role_id: int = (await cursor.fetchone())[0]
            
        member_role = discord.utils.find(lambda c: c.id == member_role_id, interaction.guild.roles)

        await interaction.response.send_message(f"{member.mention} haz been accepted 😎")
        await member.add_roles(member_role)
        await thread.edit(archived=True, locked=True)
        del self.threads[thread]

    @discord.app_commands.command(name="reject", description="Reject this user from joining the server.")
    @discord.app_commands.guild_only()
    async def reject_user(self, interaction: discord.Interaction):
        
        if interaction.channel not in self.threads.keys():
            await interaction.response.send_message("gotta do this in a thred!", ephemeral=True)
            return
        
        thread: discord.Thread = interaction.channel
        member = self.threads[thread]

        await interaction.response.send_message(f"{member} haz been rejected")
        await member.kick()
        await thread.edit(archived=True, locked=True)
        del self.threads[thread]


async def setup(bot: toof.ToofBot):
    await bot.add_cog(WelcomeCog(bot))