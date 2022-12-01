"""Extension that implements the really cool Toof Pic system. Users get
a pic using /pic roll, then receive a random pic of a certain rarity. Then
they can see their entire collection using /pic collection. Or steal from
others using /pic steal.
"""

from random import randint

import discord

import toof
from toof.pics import PicRarity, ToofPic, Collection

                
class CollectionSelect(discord.ui.Select):
    """Drop down menu to select the page for Toof pic collection."""

    def __init__(self, collection: Collection, *args, **kwargs):
        
        options = [
            discord.SelectOption(
                label=page.name.capitalize(),
                value=page.name,
                description=page.description,
                emoji=page.emoji,
                default=(collection.page == page)
            ) for page in [PicRarity.overview] + PicRarity.list()
        ]
        
        super().__init__(options=options, *args, **kwargs)
        self.collection = collection

    async def callback(self, interaction: discord.Interaction):
        """Changes the page of the menu to the selected option."""
        
        self.collection.page = self.values[0]
                
        await interaction.response.edit_message(
            content=self.collection.cur_content,
            embed=self.collection.cur_embed,
            view=CollectionView(self.collection))


class ChangePicButton(discord.ui.Button):
    """Changes the current Toof Pic on the message. Functionality
    is based on the emoji given when initializing.
    """

    def __init__(self, collection: Collection, *args, **kwargs):
        super().__init__(
            disabled=(len(collection.cur_pics) < 2),
            *args, **kwargs)
        self.collection = collection

    async def callback(self, interaction: discord.Interaction):
        """Edits the embed to show the next pic."""

        if self.emoji.name == "⏪":
            self.collection.index -= 1
        else:
            self.collection.index += 1

        await interaction.response.edit_message(
            content=self.collection.cur_content,
            embed=self.collection.cur_embed,
            view=CollectionView(self.collection))


class ShareButton(discord.ui.Button):
    """Shares the currently selected pic into the interaction
    channel.
    """

    def __init__(self, collection: Collection, *args, **kwargs):
        super().__init__(
            style=discord.ButtonStyle.primary, label="Share",
            disabled=(
                collection.page != PicRarity.overview
                and not collection.cur_pics),
            emoji="⤴️", *args, **kwargs)
        self.collection = collection

    async def callback(self, interaction: discord.Interaction):
        """Sends the selected Toof Pic into the interaction channel
        with a note that it belongs to the user.
        """
    
        await interaction.channel.send(embed=self.collection.cur_embed)
        await interaction.response.defer()


class CollectionView(discord.ui.View):
    """Contains a page select button, and buttons to navigate the
    page.
    """

    def __init__(self, collection: Collection, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_item(CollectionSelect(collection, row=0))
        self.add_item(ChangePicButton(collection, emoji="⏪", row=1))
        self.add_item(ChangePicButton(collection, emoji="⏩", row=1))
        self.add_item(ShareButton(collection, row=1))


class PicCommandGroup(discord.app_commands.Group):

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="pic",
            description="Commands relating to ToofPics.",
            guild_only=True)
        self.bot = bot

    @discord.app_commands.command(
        name="roll",
        description="Get a random ToofPic.")
    @discord.app_commands.checks.cooldown(1, 5)
    async def pic_roll(self, interaction: discord.Interaction):
        """Selects a rarity based on chance, opens that a file of that
        rarity, and sends it.
        """

        all_pics = await self.bot.get_pics()
        pic = all_pics.get_random()
        pic.dt = interaction.created_at

        collection = await self.bot.get_collection(interaction.user, all_pics)
        if pic not in collection.pics:
            query = f"""
                INSERT INTO pics
                VALUES (
                    {interaction.user.id}, '{pic.id}', '{pic.name}',
                    '{pic.link}', '{pic.date}')"""
            await self.bot.db.execute(query)
            await self.bot.db.commit()

        await interaction.response.send_message(embed=pic.embed)

    @discord.app_commands.command(
        name="steal",
        description="Try to steal a ToofPic from another user.")
    @discord.app_commands.checks.cooldown(1, 60)
    async def pic_steal(
            self, interaction: discord.Interaction,
            target: discord.User):
        """Selects a random pic from the target user's collection and
        adds it to the command user's collection if it is not already
        owned.
        """

        if randint(1, 3) != 3:
            await interaction.response.send_message(
                "you failed.", ephemeral=True)
            return
        if target == interaction.user:
            await interaction.response.send_message(
                "u cant steal from urself!", ephemeral=True)
            return

        all_pics = await self.bot.get_pics()
        user_collection = await self.bot.get_collection(
            interaction.user, all_pics)
        target_collection = await self.bot.get_collection(
            target, all_pics)
        
        if not target_collection.pics:
            await interaction.response.send_message(
                f"{target.mention} doesn't have any pics to steal !", ephemeral=True)
            return

        pic = target_collection.pics.get_random()
        
        if pic in user_collection.pics:
            content = f"u tried to steal a {pic.id} from {target.mention}, but u already hav 1!"
            ephemeral = True
        else:
            content = f"{interaction.user.mention} stole a {pic.id} from {target.mention} !"
            ephemeral = False

            query = f"""
                UPDATE pics
                SET
                    user_id = {interaction.user.id},
                    date = '{interaction.created_at.strftime("%H:%M %m/%d/%Y")}'
                WHERE
                    user_id = {target.id} AND
                    pic_id = '{pic.id}'"""
            await self.bot.db.execute(query)
            await self.bot.db.commit()
        
        await interaction.response.send_message(
            content=content, embed=pic.embed, ephemeral=ephemeral)

    @discord.app_commands.command(
        name="collection",
        description="See what Toof pics you've collected.")
    async def pic_collection(self, interaction: discord.Interaction):
        """Allows users to see their own collection of pics."""

        collection = await self.bot.get_collection(interaction.user)
        
        await interaction.response.send_message(
            embed=collection.cur_embed,
            view=CollectionView(collection),
            ephemeral=True)

    async def on_error(
            self, interaction: discord.Interaction,
            error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                content=f"slow down!!! ({error.retry_after:.2f}s)", ephemeral=True)


class PicAddCommand(discord.app_commands.Command):
    """Adds a new pic to the database, only usable by me."""

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="pic-add",
            description="Add a new Toof pic with a given image link.",
            callback=self.callback)
        self.on_error = self.error
        self.bot = bot

    @discord.app_commands.describe(
        rarity="The rarity of the new ToofPic.",
        name="What the new ToofPic will be called.",
        link="A link to the ToofPic's image.")
    @discord.app_commands.choices(
        rarity=[
            discord.app_commands.Choice(
                name=rarity.name.capitalize(),
                value=rarity.name[0].upper())
            for rarity in PicRarity.list()
        ])
    # Change this to your account's user id:
    @discord.app_commands.check(lambda i: i.user.id == 243845903146811393)
    async def callback(
            self, interaction: discord.Interaction,
            rarity: discord.app_commands.Choice[str], name: str, link: str):
        
        all_pics = await self.bot.get_pics()
        id = f"{rarity.value}{(len(all_pics)+1):03d}"
        date = interaction.created_at.strftime("%H:%M %m/%d/%Y")

        query = f"""
            INSERT INTO pics 
            VALUES (0, '{id}', '{name}', '{link}', '{date}')"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        pic = ToofPic(id, name, link, date)
        await interaction.response.send_message(
            content="pic added:",
            embed=pic.embed,
            ephemeral=True)

    async def error(
            self, _, interaction: discord.Interaction,
            error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.CheckFailure):
            await interaction.response.send_message(
                "u cant do that!", ephemeral=True)
        else:
            raise error


class CheckCollectionContext(discord.app_commands.ContextMenu):
    """Lets users see others' ToofPic Collections via context menu."""

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="Check Collection",
            callback=self.callback)
        self.bot = bot

    async def callback(
            self, interaction: discord.Interaction,
            member: discord.Member):
        
        collection = await self.bot.get_collection(member)
        
        if collection.pics:
            content = None
            embed = collection.cur_embed
        else:
            content = f"{member.name} hasznt found any ToofPics :("
            embed = None

        await interaction.response.send_message(
            content=content,
            embed=embed,
            ephemeral=True)


async def setup(bot: toof.ToofBot):
    bot.tree.add_command(PicCommandGroup(bot))
    bot.tree.add_command(PicAddCommand(bot))
    bot.tree.add_command(CheckCollectionContext(bot))
    