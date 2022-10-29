"""Extension that allows users to assign roles to themselves, and
allows moderators to create new roles with descriptions and emojis for
the users to give to themselves.
"""

from dataclasses import dataclass

import discord
from discord.ext.commands import Cog
from emoji import is_emoji

import toof


@dataclass
class ConfigRole:
    """Class containing a discord role and information for the roles
    menu.
    """
    
    role: discord.Role
    emoji: discord.PartialEmoji
    description: str
    type: str


class RoleMenu(list[ConfigRole]):
    """A list of ConfigRoles for the given guild that also contains a
    "page" attribute.
    """

    def __init__(self, list: list[ConfigRole] = None):
        super().__init__(list)
        self.page = "pings"

    @classmethod
    async def from_db(cls, bot: toof.ToofBot, guild: discord.Guild):
        """Queries the database to build a role menu for the given
        guild.
        """

        query = f"SELECT * FROM roles WHERE guild_id = {guild.id}"
        async with bot.db.execute(query) as cursor:
            list = [
                ConfigRole(
                    role=discord.utils.find(
                        lambda r: r.id == row[1], guild.roles),
                    emoji=discord.PartialEmoji.from_str(row[2]),
                    description=row[3],
                    type=row[4])
                async for row in cursor]
        
        return cls(list)

    @property
    def current(self) -> list[ConfigRole]:
        return [conf_role for conf_role in self if conf_role.type == self.page]


class RoleAddSelect(discord.ui.Select):
    """discord.ui.Select for the given role_type that contains a list
    of roles that users can add to themselves.
    """

    def __init__(
            self, interaction: discord.Interaction,
            role_menu: RoleMenu, *args, **kwargs):
    
        options = [
            discord.SelectOption(
                default=(conf_role.role in interaction.user.roles),
                label=conf_role.role.name,
                value=str(conf_role.role.id),
                description=conf_role.description,
                emoji=conf_role.emoji)
            for conf_role in role_menu.current]
        
        super().__init__(
            placeholder="Select Some Roles!",
            min_values=0,
            max_values=len(options),
            options=options,
            *args, **kwargs)

        self.role_menu = role_menu

    async def callback(self, interaction: discord.Interaction):
        """Removes roles that the user didn't select and adds the roles
        that they did select from the menu.
        """
        for role in [cr.role for cr in self.role_menu.current]:
            if str(role.id) in self.values:
                await interaction.user.add_roles(role)
            else:
                await interaction.user.remove_roles(role)
        await interaction.response.defer()


class RoleAddButton(discord.ui.Button):
    """A button to be added to the RoleAddView that changes the current
    page.
    """

    def __init__(self, role_menu: RoleMenu, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_menu = role_menu

    async def callback(self, interaction: discord.Interaction):
        """Changes the page of the menu to that of the button."""
        self.role_menu.page = self.label.lower()
        await interaction.response.edit_message(
            view=RoleAddView(interaction, self.role_menu))


class RoleAddView(discord.ui.View):
    """View that contains three RoleAddButtons for different role
    categories and a discord.ui.Select to select roles.
    """

    def __init__(
            self, interaction: discord.Interaction,
            role_menu: RoleMenu, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.add_item(RoleAddButton(
            role_menu=role_menu,
            style=(discord.ButtonStyle.primary if role_menu.page == "pings"
                else discord.ButtonStyle.secondary),
            label="Pings",
            emoji="🔔",
            row=0))
        self.add_item(RoleAddButton(
            role_menu=role_menu,
            style=(discord.ButtonStyle.primary if role_menu.page == "gaming"
                else discord.ButtonStyle.secondary),
            label="Gaming",
            emoji="🎮",
            row=0))
        self.add_item(RoleAddButton(
            role_menu=role_menu,
            style=(discord.ButtonStyle.primary if role_menu.page == "pronouns"
                else discord.ButtonStyle.secondary),
            label="Pronouns",
            emoji="😊",
            row=0
        ))

        if role_menu.current:
            self.add_item(RoleAddSelect(interaction, role_menu, row=1))


class RoleCreateModal(discord.ui.Modal):
    """Modal to be sent to moderators that creates a new role."""

    def __init__(self, bot: toof.ToofBot, role_type: str, *args, **kwargs):
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
        query = f"""
            INSERT INTO roles 
            VALUES (
                {interaction.guild_id}, {role.id}, '{self.emoji.value}',
                '{self.description.value}', '{self.role_type}')"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            content=f"made {role.mention}!",
            ephemeral=True)


class RoleDeleteSelect(discord.ui.Select):
    """discord.ui.Select that lists roles for moderators to delete."""

    def __init__(self, role_menu: RoleMenu, *args, **kwargs):
        
        options = [
            discord.SelectOption(
                label=config_role.role.name,
                value=str(config_role.role.id),
                description=config_role.description,
                emoji="❌")
            for config_role in role_menu.current]
        
        super().__init__(
            placeholder="Choose a role to delete.", min_values=0,
            max_values=1, options=options, row=1, *args, **kwargs)

        self.role_menu = role_menu

    async def callback(self, interaction: discord.Interaction):
        """Asks the user to confirm if they wish to delete the role."""

        role = discord.utils.find(
            lambda r: r.id == int(self.values[0]),
            [cr.role for cr in self.role_menu.current])
        await interaction.response.edit_message(
            content=f"delete {role.mention}?",
            view=RoleDeleteConfirmView(role),)


class RoleDeleteView(discord.ui.View):
    """View that contains the RoleDeleteSelect menu."""

    def __init__(self, role_menu: RoleMenu, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_item(RoleDeleteSelect(role_menu))


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


class RolesCommand(discord.app_commands.Command):
    """Sends the user the roles add menu."""

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="roles",
            description="Give yourself some roles. Take away some roles. Yeah.",
            callback=self.callback)
        self.guild_only = True
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        guild_role_menu = await RoleMenu.from_db(self.bot, interaction.guild)
        await interaction.response.send_message(
            view=RoleAddView(interaction, guild_role_menu),
            ephemeral=True)


class RolesConfig(discord.app_commands.Group):
    """Config for roles that lets moderators create and delete new
    roles.
    """

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="roles",
            description="Config commands relating to the roles functionality.")
        self.bot = bot

    @discord.app_commands.command(
        name="create",
        description="Create a role that users can give themselves.")
    @discord.app_commands.choices(type=[
        discord.app_commands.Choice(name="Pings", value=1),
        discord.app_commands.Choice(name="Gaming", value=2),
        discord.app_commands.Choice(name="Pronouns", value=3)])
    @discord.app_commands.describe(type="What type of role to create.")
    async def createrole_command(
            self, interaction: discord.Interaction,
            type: discord.app_commands.Choice[int]):
        """Sends the user a modal to create a new role of a given
        type.
        """
        
        await interaction.response.send_modal(
            RoleCreateModal(
                self.bot, type.name.lower(),
                title=f"Create a new {type.name} role:"))
    
    @discord.app_commands.command(
        name="delete",
        description="Get rid of a certain role.")
    @discord.app_commands.choices(type=[
        discord.app_commands.Choice(name="Pings", value=1),
        discord.app_commands.Choice(name="Gaming", value=2),
        discord.app_commands.Choice(name="Pronouns", value=3)])
    @discord.app_commands.describe(type="What type of role to delete.")
    async def deleterole_command(
            self, interaction: discord.Interaction,
            type: discord.app_commands.Choice[int]):
        """Sends the user a menu to select a role to delete."""
        
        guild_role_menu = await RoleMenu.from_db(self.bot, interaction.guild)
        guild_role_menu.page = type.name.lower()
        
        await interaction.response.send_message(
            view=RoleDeleteView(guild_role_menu),
            ephemeral=True)


class RolesCog(Cog):

    def __init__(self, bot: toof.ToofBot):
        bot.tree.add_command(RolesCommand(bot))
        self.bot = bot

    @Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        query = f"DELETE FROM roles WHERE role_id = {role.id}"
        await self.bot.db.execute(query)
        await self.bot.db.commit()


async def setup(bot: toof.ToofBot):
    await bot.add_cog(RolesCog(bot))
