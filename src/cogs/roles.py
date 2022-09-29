"""
Extension that allows users to assign roles to themselves, and allows
moderators to create new roles with descriptions and emojis for the
users to give to themselves.
"""

from dataclasses import dataclass

import discord
from discord.ext import commands
from emoji import is_emoji

import toof


@dataclass
class ConfigRole:
    """Class containing a role and information on that role."""
    role: discord.Role
    description: str
    emoji: discord.PartialEmoji


class RoleAddSelect(discord.ui.Select):
    """Drop down menu for the given category that contains roles users can add."""

    def __init__(self, interaction: discord.Interaction, roles: dict[str, list[ConfigRole]], role_type: str, *args, **kwargs):
        """
        The bot argument is used for finding the config roles.
        The role_type is the category (pings, gaming, pronouns).
        """

        # The options for the select menu are constructed by taking the config roles
        # from the bots config for the given role type.
        options = [
            discord.SelectOption(
                default=(config_role.role in interaction.user.roles),
                label=config_role.role.name,
                value=str(config_role.role.id),
                description=config_role.description,
                emoji=config_role.emoji
            ) for config_role in roles[role_type]
        ]
        
        # The select menu is initialized with the options shown above.
        super().__init__(
            placeholder="Select Some Roles!",
            min_values=0,
            max_values=len(options),
            options=options,
            row=1,
            *args, **kwargs
        )

        # A list of roles is created to make assigning user roles simpler in the callback.
        self.role_list = [config_role.role for config_role in roles[role_type]]

    async def callback(self, interaction: discord.Interaction):
        # Removes the roles from the user that they did not select,
        # and adds roles to the user that they did select.
        for role in self.role_list:
            if str(role.id) not in self.values:
                await interaction.user.remove_roles(role)
            if str(role.id) in self.values:
                await interaction.user.add_roles(role)
        await interaction.response.defer()

class RoleAddButton(discord.ui.Button):
    """A button to be added to the RolesView that changes the page."""

    def __init__(self, roles: dict[str, list[ConfigRole]], role_type: str,*args, **kwargs):
        """
        The bot argument is used for finding the config roles.
        The role_type is the category (pings, gaming, pronouns).
        """
        
        super().__init__(*args, **kwargs)
        self.roles = roles
        self.role_type = role_type

    async def callback(self, interaction: discord.Interaction):
        # Edits the original response by updating the view to reflect the chosen page.
        await interaction.response.edit_message(
            view=RoleAddView(interaction, self.roles, self.role_type)
        )

class RoleAddView(discord.ui.View):
    """View that contains three buttons for different role categories and a menu to select roles."""

    def __init__(self, interaction: discord.Interaction, roles: dict[str, list[ConfigRole]], role_type: str, *args, **kwargs):
        """
        Creates a view highlighting the page of the given role_type (pings, gaming, pronouns).
        The bot argument is used to pass along the config and config roles.
        """
        super().__init__(*args, **kwargs)
        
        if role_type == 'pings':
            pings_style = discord.ButtonStyle.primary
            gaming_style = discord.ButtonStyle.secondary
            pronouns_style = discord.ButtonStyle.secondary
        
        if role_type == 'gaming':
            pings_style = discord.ButtonStyle.secondary
            gaming_style = discord.ButtonStyle.primary
            pronouns_style = discord.ButtonStyle.secondary

        if role_type == 'pronouns':
            pings_style = discord.ButtonStyle.secondary
            gaming_style = discord.ButtonStyle.secondary
            pronouns_style = discord.ButtonStyle.primary
        
        self.add_item(RoleAddButton(
            roles=roles,
            role_type='pings',

            style=pings_style,
            label="Pings",
            emoji="🔔",
            row=0
        ))
        self.add_item(RoleAddButton(
            roles=roles,
            role_type='gaming',

            style=gaming_style,
            label="Gaming",
            emoji="🎮",
            row=0
        ))
        self.add_item(RoleAddButton(
            roles=roles,
            role_type='pronouns',

            style=pronouns_style,
            label="Pronouns",
            emoji="😊",
            row=0
        ))

        self.add_item(RoleAddSelect(interaction, roles, role_type))


class RoleCreateModal(discord.ui.Modal):
    """Modal to be sent to moderators that creates a new role."""

    def __init__(self, bot: toof.ToofBot, role_type: str, *args, **kwargs):
        """
        The bot argument is used for finding the config roles to be appended to, 
        as well as the config file.
        The role_type is the category (pings, gaming, pronouns) that the role will be appended to.
        """
        
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.role_type = role_type
        
    name = discord.ui.TextInput(
        label="Role Name", 
        style=discord.TextStyle.short, 
        placeholder="ex: Fortnite, Minecraft, etc...",
        min_length=1,
        max_length=20
    ) 
    color = discord.ui.TextInput(
        label="Color",
        style=discord.TextStyle.short,
        placeholder="#ffffff",
        min_length=7,
        max_length=7
    )
    emoji = discord.ui.TextInput(
        label="Emoji",
        style=discord.TextStyle.short,
        placeholder="Emoji to represent this role in menus.",
        min_length=1
    )
    description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.long,
        placeholder="What is this role for?",
        min_length=1,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        
        # Ensures emoji is valid unicode emoji.
        if not is_emoji(self.emoji.value):
            await interaction.response.send_message(
                content="Invalid emoji. Try again.",
                ephemeral=True
            )
            return

        # Ensures color was formatted properly.
        try:
            color = discord.Color.from_str(self.color.value)
        except ValueError:
            await interaction.response.send_message(
                content="wats that color??? (Invalid color code. Try again. Accepts hex format `#ffffff`).",
                ephemeral=True
            )
            return

        # Creates the role on the server from the given input.
        role = await interaction.guild.create_role(
            name=self.name.value, 
            color=color,
            mentionable=(self.role_type == "gaming")
        )

        # Updates the database with the role's info.
        await self.bot.db.execute(f'INSERT INTO roles VALUES ({interaction.guild_id}, {role.id}, {self.emoji.value}, {self.description.value}, {self.role_type})')
        await self.bot.db.commit()

        await interaction.response.send_message(content=f"made {role.mention}!", ephemeral=True)


class RoleDeleteSelect(discord.ui.Select):
    """Select menu that will prompt user to delete a certain role."""

    def __init__(self, roles: dict[str, list[ConfigRole]], role_type: str, *args, **kwargs):
        """
        The bot argument is used for finding the config roles.
        The role_type is the category (pings, gaming, pronouns).
        """
        
        # The options for the select menu are constructed by taking the config roles
        # from the bots config for the given role type.
        options = [
            discord.SelectOption(
                label=config_role.role.name,
                value=str(config_role.role.id),
                description=config_role.description,
                emoji="❌"
            ) for config_role in roles[role_type]
        ]
        
        # The select menu is initialized with the options shown above.
        super().__init__(
            placeholder="Choose a role to delete.",
            min_values=0,
            max_values=1,
            options=options,
            row=1,
            *args, **kwargs
        )

        # A list of roles is created to make assigning user roles simpler in the callback.
        self.role_list = [config_role.role for config_role in roles[role_type]]

    async def callback(self, interaction: discord.Interaction):
        # Finds the role object to delete from the list of roles created in __init__,
        # Then prompts the user if they really want to delete that role.
        role = discord.utils.find(lambda r: r.id == int(self.values[0]), self.role_list)
        await interaction.response.edit_message(
            content=f"delete {role.mention}?",
            view=RoleDeleteConfirmView(role),
        )

class RoleDeleteView(discord.ui.View):
    """View that contains the RoleDeleteSelect menu."""

    def __init__(self, roles: dict[str, list[ConfigRole]], role_type: str, *args, **kwargs):
        """Creates a view with a select menu to choose the role to delete."""
        
        super().__init__(*args, **kwargs)
        self.add_item(RoleDeleteSelect(roles=roles, role_type=role_type))

class RoleDeleteConfirmView(discord.ui.View):
    """View containing two buttons that prompt whether to delete the selected role."""

    def __init__(self, role: discord.Role, *args, **kwargs):
        """
        Creates a view with two buttons prompting the user to confirm the given role's deletion
        The bot argument is passed along to provide the config role dictionary and the config filename.
        """
        
        super().__init__(*args, **kwargs)
        self.role = role

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.green,
        emoji="✔️"
    )
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.Button):
        """Deletes the role from the bot's dictionary, the server, and the config file."""

        await self.role.delete()
        await interaction.response.edit_message(
            content=f"deleted `{self.role.name}`.",
            view=None
        )
        
    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.red,
        emoji="✖️"
    )
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.Button):
        """Aborts the deletion."""
        
        await interaction.response.edit_message(
            content=f"didnt delete {self.role.mention}",
            view=None
        )


class RolesCog(commands.Cog):
    """Cog containing commands relating to roles."""

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
        
    async def get_guild_role_dict(self, interaction: discord.Interaction) -> dict[str, list[ConfigRole]]:
        """Queries the database to build a dictionary of config roles for the given interaction's guild."""
        
        async with self.bot.db.execute(f'SELECT * FROM roles WHERE guild_id = {interaction.guild_id}') as cursor:
            guild_role_records = await cursor.fetchall()

        guild_roles_dict: dict[str, list[ConfigRole]] = {'pings': [], 'gaming': [], 'pronouns': []}
        for record in guild_role_records:

            role: discord.Role = discord.utils.find(lambda r: r.id == record[1], interaction.guild.roles)
            emoji = discord.PartialEmoji.from_str(record[2])
            description: str = record[3]

            guild_roles_dict[record[4]].append(ConfigRole(role, description, emoji))

        return guild_roles_dict

    @discord.app_commands.command(name="roles", description="Give yourself some roles. Take away some roles. Yeah.")
    @discord.app_commands.guild_only()
    async def role_menu(self, interaction: discord.Interaction):
        """Sends the user the role add menu."""
        
        guild_roles_dict = await self.get_guild_role_dict(interaction)
        await interaction.response.send_message(
            view=RoleAddView(interaction, guild_roles_dict, 'pings'),
            ephemeral=True
        )

    @discord.app_commands.command(name="createrole", description="Create a role that users can give themselves.")
    @discord.app_commands.choices(
        type=[
            discord.app_commands.Choice(name="Pings", value=1),
            discord.app_commands.Choice(name="Gaming", value=2),
            discord.app_commands.Choice(name="Pronouns", value=3),
        ]
    )
    @discord.app_commands.describe(type="What type of role to create.")
    @discord.app_commands.guild_only()
    async def create_role(self, interaction: discord.Interaction, type: discord.app_commands.Choice[int]):
        """Sends the user a modal to create a new role of a given type."""
        
        await interaction.response.send_modal(RoleCreateModal(self.bot, type.value.lower(), title=f"Create a new {type.name} role:"))
    
    @discord.app_commands.command(name="deleterole", description="Get rid of a certain role.")
    @discord.app_commands.choices(
        type=[
            discord.app_commands.Choice(name="Pings", value=1),
            discord.app_commands.Choice(name="Gaming", value=2),
            discord.app_commands.Choice(name="Pronouns", value=3),
        ]
    )
    @discord.app_commands.describe(type="What type of role to delete.")
    @discord.app_commands.guild_only()
    async def delete_role(self, interaction: discord.Interaction, type: discord.app_commands.Choice[int]):
        """Sends the user a menu to select a role to delete."""
        
        guild_roles_dict = await self.get_guild_role_dict(interaction)
        await interaction.response.send_message(
            view=RoleDeleteView(guild_roles_dict, type.name.lower()),
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Removes the role from the config if it was created through commands."""

        async with self.bot.db.execute(f'SELECT role_id FROM roles WHERE guild_id = {role.guild.id}') as cursor:
            role_ids = [record[0] for record in await cursor.fetchall()]

        if role.id in role_ids:
            await self.bot.db.execute(f'DELETE FROM roles WHERE role_id = {role.id}')
            await self.bot.db.commit()


async def setup(bot: toof.ToofBot):
    await bot.add_cog(RolesCog(bot))
