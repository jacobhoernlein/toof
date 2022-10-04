"""Extension that allows users to assign roles to themselves, and
allows moderators to create new roles with descriptions and emojis for
the users to give to themselves.
"""

from dataclasses import dataclass

import discord
from discord.ext import commands
from emoji import is_emoji

from .. import base


@dataclass
class ConfigRole:
    """Class containing a discord role and information for the roles
    menu.
    """
    
    role: discord.Role
    description: str
    emoji: discord.PartialEmoji


class RoleAddSelect(discord.ui.Select):
    """discord.ui.Select for the given role_type that contains a list
    of roles that users can add to themselves.
    """

    def __init__(
            self, interaction: discord.Interaction,
            role_dict: dict[str, list[ConfigRole]],
            role_type: str, *args, **kwargs):
    
        options = [
            discord.SelectOption(
                default=(config_role.role in interaction.user.roles),
                label=config_role.role.name,
                value=str(config_role.role.id),
                description=config_role.description,
                emoji=config_role.emoji)
            for config_role in role_dict[role_type]]
        
        super().__init__(
            placeholder="Select Some Roles!",
            min_values=0,
            max_values=len(options),
            options=options,
            *args, **kwargs)

        # Creates a list of roles relating to the current page.
        self.role_list = [conf_role.role for conf_role in role_dict[role_type]]

    async def callback(self, interaction: discord.Interaction):
        """Removes roles that the user didn't select and adds the roles
        that they did select from the menu.
        """

        for role in self.role_list:
            if str(role.id) not in self.values:
                await interaction.user.remove_roles(role)
            if str(role.id) in self.values:
                await interaction.user.add_roles(role)
        await interaction.response.defer()


class RoleAddButton(discord.ui.Button):
    """A button to be added to the RoleAddView that changes the current
    page.
    """

    def __init__(
            self, role_dict: dict[str, list[ConfigRole]],
            role_type: str,*args, **kwargs):
        super().__init__(*args, **kwargs)

        self.role_dict = role_dict
        self.role_type = role_type

    async def callback(self, interaction: discord.Interaction):
        """Changes the page of the menu to that of the button."""

        await interaction.response.edit_message(
            view=RoleAddView(interaction, self.role_dict, self.role_type))


class RoleAddView(discord.ui.View):
    """View that contains three RoleAddButtons for different role
    categories and a discord.ui.Select to select roles.
    """

    def __init__(
            self, interaction: discord.Interaction,
            role_dict: dict[str, list[ConfigRole]],
            role_type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if role_type == "pings":
            pings_style = discord.ButtonStyle.primary
            gaming_style = discord.ButtonStyle.secondary
            pronouns_style = discord.ButtonStyle.secondary
        
        if role_type == "gaming":
            pings_style = discord.ButtonStyle.secondary
            gaming_style = discord.ButtonStyle.primary
            pronouns_style = discord.ButtonStyle.secondary

        if role_type == "pronouns":
            pings_style = discord.ButtonStyle.secondary
            gaming_style = discord.ButtonStyle.secondary
            pronouns_style = discord.ButtonStyle.primary
        
        self.add_item(RoleAddButton(
            role_dict=role_dict,
            role_type="pings",
            style=pings_style,
            label="Pings",
            emoji="🔔",
            row=0))
        self.add_item(RoleAddButton(
            role_dict=role_dict,
            role_type="gaming",
            style=gaming_style,
            label="Gaming",
            emoji="🎮",
            row=0))
        self.add_item(RoleAddButton(
            role_dict=role_dict,
            role_type="pronouns",
            style=pronouns_style,
            label="Pronouns",
            emoji="😊",
            row=0
        ))

        if role_dict[role_type]:
            self.add_item(RoleAddSelect(
                interaction, role_dict, role_type,
                row=1))


class RoleCreateModal(discord.ui.Modal):
    """Modal to be sent to moderators that creates a new role."""

    def __init__(self, bot: base.Bot, role_type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bot = bot
        self.role_type = role_type
        
    name = discord.ui.TextInput(
        label="Role Name", 
        style=discord.TextStyle.short, 
        placeholder="ex: Fortnite, Minecraft, etc...",
        min_length=1,
        max_length=20) 
    color = discord.ui.TextInput(
        label="Color",
        style=discord.TextStyle.short,
        placeholder="#ffffff",
        min_length=7,
        max_length=7)
    emoji = discord.ui.TextInput(
        label="Emoji",
        style=discord.TextStyle.short,
        placeholder="Emoji to represent this role in menus.",
        min_length=1)
    description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.long,
        placeholder="What is this role for?",
        min_length=1,
        max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        """Creates the role in the server and adds its info to the
        database.
        """

        # Ensures emoji is valid unicode emoji.
        if not is_emoji(self.emoji.value):
            await interaction.response.send_message(
                content="Invalid emoji. Try again.",
                ephemeral=True)
            return

        # Ensures color was formatted properly.
        try:
            color = discord.Color.from_str(self.color.value)
        except ValueError:
            await interaction.response.send_message(
                content="wats that color??? (Invalid color code. Try again. Accepts hex format `#ffffff`).",
                ephemeral=True)
            return

        # Creates the role on the server from the given input.
        role = await interaction.guild.create_role(
            name=self.name.value, 
            color=color,
            mentionable=(self.role_type == "gaming"))

        # Updates the database with the role's info.
        query = f"INSERT INTO roles VALUES ({interaction.guild_id}, {role.id}, {self.emoji.value}, {self.description.value}, {self.role_type})"
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            content=f"made {role.mention}!",
            ephemeral=True)


class RoleDeleteSelect(discord.ui.Select):
    """discord.ui.Select that lists roles for moderators to delete."""

    def __init__(
            self, role_dict: dict[str, list[ConfigRole]],
            role_type: str, *args, **kwargs):
        
        options = [
            discord.SelectOption(
                label=config_role.role.name,
                value=str(config_role.role.id),
                description=config_role.description,
                emoji="❌")
            for config_role in role_dict[role_type]]
        
        super().__init__(
            placeholder="Choose a role to delete.", min_values=0,
            max_values=1, options=options, row=1, *args, **kwargs)

        # Creates a list of roles relating to the given type
        self.role_list = [conf_role.role for conf_role in role_dict[role_type]]

    async def callback(self, interaction: discord.Interaction):
        """Asks the user to confirm if they wish to delete the role."""

        role = discord.utils.find(
            lambda r: r.id == int(self.values[0]),
            self.role_list)
        await interaction.response.edit_message(
            content=f"delete {role.mention}?",
            view=RoleDeleteConfirmView(role),)


class RoleDeleteView(discord.ui.View):
    """View that contains the RoleDeleteSelect menu."""

    def __init__(
            self, role_dict: dict[str, list[ConfigRole]],
            role_type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_item(RoleDeleteSelect(role_dict, role_type))


class RoleDeleteConfirmView(discord.ui.View):
    """View containing two buttons that prompt whether to delete the
    selected role.
    """

    def __init__(self, role: discord.Role, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.role = role

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.green,
        emoji="✔️")
    async def confirm_delete(
            self, interaction: discord.Interaction,
            button: discord.Button):
        """Deletes the role."""

        await self.role.delete()
        await interaction.response.edit_message(
            content=f"deleted `{self.role.name}`.",
            view=None)
        
    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.red,
        emoji="✖️")
    async def cancel_delete(
            self, interaction: discord.Interaction,
            button: discord.Button):
        """Doesn't delete the role."""

        await interaction.response.edit_message(
            content=f"didnt delete {self.role.mention}",
            view=None)


class RolesCog(base.Cog):
    """Cog containing commands relating to roles."""
 
    async def get_role_dict(
            self,
            guild: discord.Guild) -> dict[str, list[ConfigRole]]:
        """Creates the role_dict for the guild by querying the
        database.
        """
        
        guild_roles_dict = {"pings": [], "gaming": [], "pronouns": []}
        
        query = f'SELECT * FROM roles WHERE guild_id = {guild.id}'
        async with self.bot.db.execute(query) as cursor:
            async for row in cursor:

                role: discord.Role = discord.utils.find(
                    lambda r: r.id == row[1],
                    guild.roles)
                emoji = discord.PartialEmoji.from_str(row[2])
                description: str = row[3]

                guild_roles_dict[row[4]].append(
                    ConfigRole(role, description, emoji))

        return guild_roles_dict

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Removes the role from the config if it was created through
        commands.
        """

        await self.bot.db.execute(f'DELETE FROM roles WHERE role_id = {role.id}')
        await self.bot.db.commit()

    @discord.app_commands.command(
        name="roles",
        description="Give yourself some roles. Take away some roles. Yeah.")
    @discord.app_commands.guild_only()
    async def roles_command(self, interaction: discord.Interaction):
        """Sends the user the roles add menu."""
        
        guild_roles_dict = await self.get_role_dict(interaction.guild)
        await interaction.response.send_message(
            view=RoleAddView(interaction, guild_roles_dict, 'pings'),
            ephemeral=True)

    @discord.app_commands.command(
        name="createrole",
        description="Create a role that users can give themselves.")
    @discord.app_commands.choices(type=[
        discord.app_commands.Choice(name="Pings", value=1),
        discord.app_commands.Choice(name="Gaming", value=2),
        discord.app_commands.Choice(name="Pronouns", value=3)])
    @discord.app_commands.describe(type="What type of role to create.")
    @discord.app_commands.guild_only()
    async def createrole_command(
            self, interaction: discord.Interaction,
            type: discord.app_commands.Choice[int]):
        """Sends the user a modal to create a new role of a given
        type.
        """
        
        await interaction.response.send_modal(
            RoleCreateModal(
                self.bot, type.value.lower(),
                title=f"Create a new {type.name} role:"))
    
    @discord.app_commands.command(
        name="deleterole",
        description="Get rid of a certain role.")
    @discord.app_commands.choices(type=[
        discord.app_commands.Choice(name="Pings", value=1),
        discord.app_commands.Choice(name="Gaming", value=2),
        discord.app_commands.Choice(name="Pronouns", value=3)])
    @discord.app_commands.describe(type="What type of role to delete.")
    @discord.app_commands.guild_only()
    async def deleterole_command(
            self, interaction: discord.Interaction,
            type: discord.app_commands.Choice[int]):
        """Sends the user a menu to select a role to delete."""
        
        guild_roles_dict = await self.get_role_dict(interaction.guild)
        await interaction.response.send_message(
            view=RoleDeleteView(guild_roles_dict, type.name.lower()),
            ephemeral=True
        )
