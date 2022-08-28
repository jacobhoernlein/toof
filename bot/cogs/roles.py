"""Cog that contains functionality for users to assign themselves roles."""

import json
import discord
import toof


class RoleAddSelect(discord.ui.Select):
    """Drop down menu for the given category that contains roles users can add."""

    def __init__(self, bot: toof.ToofBot, role_type: str, *args, **kwargs):
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
                emoji=config_role.emoji
            ) for config_role in bot.config.roles[role_type]
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
        self.roles = [config_role.role for config_role in bot.config.roles[role_type]]

    async def callback(self, interaction: discord.Interaction):
        # Removes the roles from the user that they did not select,
        # and adds roles to the user that they did select.
        for role in self.roles:
            if str(role.id) not in self.values:
                await interaction.user.remove_roles(role)
            if str(role.id) in self.values:
                await interaction.user.add_roles(role)
        await interaction.response.defer()

class RoleAddButton(discord.ui.Button):
    """A button to be added to the RolesView that changes the page."""

    def __init__(self, bot: toof.ToofBot, role_type: str,*args, **kwargs):
        """
        The bot argument is used for finding the config roles.
        The role_type is the category (pings, gaming, pronouns).
        """
        
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.role_type = role_type

    async def callback(self, interaction: discord.Interaction):
        # Edits the original response by updating the view to reflect the chosen page.
        await interaction.response.edit_message(
            view=RoleAddView(self.bot, self.role_type)
        )

class RoleAddView(discord.ui.View):
    """View that contains three buttons for different role categories and a menu to select roles."""

    def __init__(self, bot: toof.ToofBot, role_type: str, *args, **kwargs):
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
            bot=bot,
            role_type='pings',

            style=pings_style,
            label="Pings",
            emoji="🔔",
            row=0
        ))
        self.add_item(RoleAddButton(
            bot=bot,
            role_type='gaming',

            style=gaming_style,
            label="Gaming",
            emoji="🎮",
            row=0
        ))
        self.add_item(RoleAddButton(
            bot=bot,
            role_type='pronouns',

            style=pronouns_style,
            label="Pronouns",
            emoji="☺️",
            row=0
        ))

        self.add_item(RoleAddSelect(bot=bot, role_type=role_type))


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
        placeholder="Fortnite, Minecraft, etc...",
        max_length=20
    ) 
    color = discord.ui.TextInput(
        label="Color",
        style=discord.TextStyle.short,
        placeholder="Hex format (#ffffff)",
        min_length=7,
        max_length=7
    )
    emoji = discord.ui.TextInput(
        label="Emoji",
        style=discord.TextStyle.short,
        placeholder="Emoji to represent this role in menus"
    )
    description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.long,
        placeholder="What is this role for?",
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        
        # Creates the role on the server from the given input.
        role = await interaction.guild.create_role(
            name=self.name.value, 
            color=discord.Color.from_str(self.color.value),
            mentionable=(self.role_type == "gaming")
        )

        # Creates a config role object and adds it to the list of the respective type.
        self.bot.config.roles[self.role_type].append(toof.ConfigRole(
            [role], 
            role.id, 
            description=self.description.value, 
            emoji=self.emoji.value
        ))

        # Creates a dict object based on the role and adds it to the config file.
        with open(self.bot.config.filename) as fp:
            config = json.load(fp)
        config['roles'][self.role_type].append(
            {
                "name": self.name.value,
                "id": int(role.id),
                "description": self.description.value,
                "emoji": self.emoji.value
            }
        )
        with open(self.bot.config.filename, "w") as fp:
            json.dump(config, fp, indent=4)

        await interaction.response.send_message(content=f"Created {role.mention}!", ephemeral=True)


class RoleDeleteSelect(discord.ui.Select):
    """Select menu that will prompt user to delete a certain role."""

    def __init__(self, bot: toof.ToofBot, role_type: str, *args, **kwargs):
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
            ) for config_role in bot.config.roles[role_type]
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
        self.roles = [config_role.role for config_role in bot.config.roles[role_type]]
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # Finds the role object to delete from the list of roles created in __init__,
        # Then prompts the user if they really want to delete that role.
        role = discord.utils.find(lambda r: r.id == int(self.values[0]), self.roles)
        await interaction.response.edit_message(
            content=f"Delete {role.mention}?",
            view=RoleDeleteConfirmView(self.bot, role),
        )

class RoleDeleteView(discord.ui.View):
    """View that contains the RoleDeleteSelect menu."""

    def __init__(self, bot: toof.ToofBot, role_type: str, *args, **kwargs):
        """Creates a view with a select menu to choose the role to delete."""
        
        super().__init__(*args, **kwargs)
        self.add_item(RoleDeleteSelect(bot=bot, role_type=role_type))

class RoleDeleteConfirmView(discord.ui.View):
    """View containing two buttons that prompt whether to delete the selected role."""

    def __init__(self, bot: toof.ToofBot, role: discord.Role, *args, **kwargs):
        """
        Creates a view with two buttons prompting the user to confirm the given role's deletion
        The bot argument is passed along to provide the config role dictionary and the config filename.
        """
        
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.role = role

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.green,
        emoji="✔️"
    )
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.Button):
        """Deletes the role from the bot's dictionary, the server, and the config file."""

        with open(self.bot.config.filename) as fp:
            config = json.load(fp)

        found_role = False
        for role_type in ['pings', 'gaming', 'pronouns']:
            # Finds the dictionary object that represents the role in the config and deletes it.
            for i in range(len(config['roles'][role_type])):
                if config['roles'][role_type][i]['id'] == self.role.id:
                    del config['roles'][role_type][i]
                    break
            # Finds the config role in the bot and removes it, as well as deletes the role from the server.
            for config_role in self.bot.config.roles[role_type]:
                if config_role.role == self.role:
                    self.bot.config.roles[role_type].remove(config_role)
                    await interaction.response.edit_message(
                        content=f"Deleted `{self.role.name}`.",
                        view=None
                    )
                    await self.role.delete()
                    found_role = True
                    break
            if found_role:
                break

        with open(self.bot.config.filename, "w") as fp:
            json.dump(config, fp, indent=4)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.red,
        emoji="✖️"
    )
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.Button):
        """Aborts the deletion."""
        
        await interaction.response.edit_message(
            content=f"Didn't delete {self.role.mention}",
            view=None
        )


async def setup(bot: toof.ToofBot):

    @bot.tree.command(name="roles", description="Give yourself some roles. Take away some roles. Yeah.")
    @discord.app_commands.guild_only()
    async def role_menu(interaction: discord.Interaction):
        """Sends the user the role add menu."""
        
        await interaction.response.send_message(
            view=RoleAddView(bot, 'pings'),
            ephemeral=True
        )

    @discord.app_commands.guild_only()
    class RoleConfig(discord.app_commands.Group):
        """Group that contains the role create and role delete commands."""

        @discord.app_commands.command(name="create", description="Create a role that users can give themselves.")
        @discord.app_commands.choices(
            type=[
                discord.app_commands.Choice(name="Pings", value=1),
                discord.app_commands.Choice(name="Gaming", value=2),
                discord.app_commands.Choice(name="Pronouns", value=3),
            ]
        )
        @discord.app_commands.describe(type="What type of role to create.")
        async def add_role(self, interaction: discord.Interaction, type: discord.app_commands.Choice[int]):
            """Sends the user a modal to create a new role of a given type."""
            
            await interaction.response.send_modal(RoleCreateModal(bot, type.name.lower(), title=f"Create a new {type.name} role:"))
    
        @discord.app_commands.command(name="delete", description="Get rid of a certain role.")
        @discord.app_commands.choices(
            type=[
                discord.app_commands.Choice(name="Pings", value=1),
                discord.app_commands.Choice(name="Gaming", value=2),
                discord.app_commands.Choice(name="Pronouns", value=3),
            ]
        )
        @discord.app_commands.describe(type="What type of role to delete.")
        async def delete_role(self, interaction: discord.Interaction, type: discord.app_commands.Choice[int]):
            """Sends the user a menu to select a role to delete."""
            
            await interaction.response.send_message(
                view=RoleDeleteView(bot, type.name.lower()),
                ephemeral=True
            )

    bot.tree.add_command(RoleConfig(name="role", description="Role creation and deletion."))
