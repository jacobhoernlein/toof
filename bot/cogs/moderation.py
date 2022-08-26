"""Moderation commands and features"""

import datetime as dt
import json
from readline import append_history_file

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
        """Logs deleted messages"""
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
        """Watches for messages that are edited"""
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
    
    @discord.app_commands.guild_only()
    class Role_Commands(discord.app_commands.Group):
        
        @discord.app_commands.command(name="list", description="List available roles.")
        async def list_roles(self, interaction:discord.Interaction):
            role_list = ""
            for role in bot.config.roles:
                role_list += f"• {role.mention}\n"

            embed = discord.Embed(
                description=role_list,
                color=discord.Color.blurple(),
            )
            embed.set_author(name="Available roles:")
            embed.set_footer(text="To give yourself a role, do /role add {rolename}.")

            await interaction.response.send_message(embed=embed, ephemeral=True)

        @discord.app_commands.command(name="add", description="Give yourself a role.")
        @discord.app_commands.describe(role="The role that you want to give yourself.")
        async def add_role(self, interaction:discord.Interaction, role:discord.Role):
            if role in bot.config.roles and role not in interaction.user.roles:
                await interaction.user.add_roles(role)
                await interaction.response.send_message("✅", ephemeral=True)
            else:
                await interaction.response.send_message("❌", ephemeral=True)

        @discord.app_commands.command(name="remove", description="Take away a role from yourself.")
        @discord.app_commands.describe(role="The role that you want to remove from yourself.")
        async def remove_role(self, interaction:discord.Interaction, role:discord.Role):
            if role in bot.config.roles and role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                await interaction.response.send_message("✅", ephemeral=True)
            else:
                await interaction.response.send_message("❌", ephemeral=True)

        @discord.app_commands.command(name="create", description="Create a new role that users can add.")
        @discord.app_commands.describe(
            name="The name for the new role.",
            color="A hex code for the role's color."
        )
        async def create_role(self, interaction:discord.Interaction, name:str, color:str):
            role = await interaction.guild.create_role(
                name=name,
                color=discord.Color.from_str(color),
                mentionable=True
            )
            await interaction.response.send_message(content=f"✅ {role.mention}", ephemeral=True)

            with open(bot.config.filename) as fp:
                config = json.load(fp)

            config['roles'].append(role.id)
            bot.config.roles.append(role)
            
            with open(bot.config.filename, 'w') as fp:
                json.dump(config, fp, indent=4)
   
    # Removes deleted roles from the config
    @bot.event
    async def on_guild_role_delete(role:discord.Role):
        if role in bot.config.roles:
            bot.config.roles.remove(role)

            with open(bot.config.filename) as fp:
                config = json.load(fp)

            try:
                config['roles'].remove(role.id)
            except KeyError:
                print(f"Could not remove {role.id} from extra roles list. Skipping.")
            else:
                with open(bot.config.filename, "w") as fp:
                    json.dump(config, fp, indent=4)

    bot.tree.add_command(Role_Commands(name="role", description="Commands relating to extra roles for games."))
