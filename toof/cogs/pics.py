"""Extension that implements the really cool Toof Pic system. Users get
a pic using /pic, then receive a random pic of a certain rarity. Then
they can see their entire collection using /pics.
"""

from dataclasses import dataclass
from datetime import datetime
import random

import discord
from discord.ext import commands

import toof


class ToofPicRarity:
    """Class representing different rarities."""

    def __init__(self, name: str, value: int, weight: float, emoji: str, description: str):
        self.name = name
        self.value = value
        self.weight = weight
        self.emoji = emoji
        self.description = description
        
    @classmethod
    @property
    def overview(cls):
        return cls(
            name="overview", value=0, weight=0, emoji="🔎",
            description="Shows an overview of your entire ToofPic collection.")

    @classmethod
    @property
    def common(cls):
        return cls(
            name="common", value=1, weight=1, emoji="🐶",
            description="Normal, run-of-the-mill ToofPics. (He is such a good boy).")

    @classmethod
    @property
    def rare(cls):
        return cls(
            name="rare", value=2, weight=0.1, emoji="💎",
            description="ToofPics of a bit higher quality. They are blue flavored.")

    @classmethod
    @property
    def legendary(cls):
        return cls(
            name="legendary", value=3, weight=0.01, emoji="⭐",
            description="The rarest, most awe-inspiring ToofPics money can buy.")

    @classmethod
    @property
    def unknown(cls):
        return cls(
            name="unknown", value=100, weight=0, emoji="❓",
            description="IDK wut these r.")

    @classmethod
    def list(cls):
        """Returns a list of all rarities."""
        return [cls.common, cls.rare, cls.legendary]

    @classmethod
    def get(cls, page: str):
        match page.lower():
            case "overview":
                return cls.overview
            case "common" | "commons":
                return cls.common
            case "rare" | "rares":
                return cls.rare
            case "legendary" | "legendaries":
                return cls.legendary
            case _:
                return cls.unknown

    def __eq__(self, other):
        if isinstance(other, ToofPicRarity):
            return self.value == other.value
        match other:
            case str(other):
                return self.name == other or self.emoji == other
            case int(other):
                return self.value == other
            case _:
                raise TypeError(f"Equality not supported between ToofPicRarity and {other.__class__}")

    def __lt__(self, other):
        if isinstance(other, ToofPicRarity):
            return self.value < other.value
        elif isinstance(other, int):
            return self.value < other
        else:
            raise TypeError(f"Less-Than not supported between ToofPicRarity and {other.__class__}")
        
    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<ToofPicRarity.{self.name}: {self.value}>"


@dataclass
class ToofPic:
    """A representation of a ToofPic. Contains an id, link, rarity,
    and embed.
    """

    id: str
    name: str
    link: str
    date: str
  
    @property
    def datetime(self) -> datetime:
        return datetime.strptime(self.date, "%H:%M %m/%d/%Y")

    @property
    def rarity(self) -> ToofPicRarity:
        match self.id[0]:
            case "C":
                return ToofPicRarity.common
            case "R":
                return ToofPicRarity.rare
            case "L":
                return ToofPicRarity.legendary
            case _:
                return ToofPicRarity.unknown

    @property
    def embed(self) -> discord.Embed:
        match self.rarity:
            case ToofPicRarity.common:
                color = discord.Color.green()
                emoji = "🐶"
            case ToofPicRarity.rare:
                color = discord.Color.blue()
                emoji = "💎"
            case ToofPicRarity.legendary:
                color = discord.Color.gold()
                emoji = "⭐"
            case ToofPicRarity.unknown:
                color = discord.Color.blurple()
                emoji = "❓"

        embed = discord.Embed(color=color)
        embed.set_author(name=f'{emoji} "{self.name}" • {self.id}')
        embed.set_image(url=self.link)
        return embed

    def __eq__(self, other: "ToofPic"):
        return self.id == other.id
        
    def __lt__(self, other: "ToofPic"):
        if self.rarity < other.rarity:
            return True
        if self.rarity > other.rarity:
            return False
        return self.id < other.id
    

class ToofPics(list[ToofPic]):
    """Subclasses a list of ToofPics and includes methods relating to
    them.
    """

    @classmethod
    async def from_db(cls, bot: toof.ToofBot):
        """Return a list of all ToofPics by referencing the database."""

        query = "SELECT * FROM pics WHERE user_id = 0"
        async with bot.db.execute(query) as cursor:
            list = [
                ToofPic(row[1], row[2], row[3], row[4])
                async for row in cursor
            ]
        return cls(list)

    def __getitem__(self, key):
        if isinstance(key, str) or isinstance(key, ToofPicRarity):
            return [pic for pic in self if pic.rarity == key]
        return super().__getitem__(key)
        
    def get_random(self) -> ToofPic:
        """Selects a random ToofPic from the list and returns it
        weighted by rarity. Raises IndexError if the list is empty.
        """

        rarities = ToofPicRarity.list()

        while True:
            # Select a rarity from the list.
            rarity = random.choices(
                population=rarities,
                weights=[rarity.weight for rarity in rarities], 
                k=1
            )[0]
            
            try:
                return random.choice(self[rarity])
            # No pics for the chosen rarity. Remove and try again.
            except IndexError:
                rarities.remove(rarity)
                
    
class Collection:
    """Object representing a user's collection of ToofPics."""

    def __init__(
            self, usr_pics: ToofPics,
            all_pics: ToofPics, user: discord.User):
        self.pics = usr_pics
        self.__overview = self.__get_overview_embed(usr_pics, all_pics, user)
        self.__page = ToofPicRarity.overview
        self.__index = 0

    @classmethod
    async def from_db(
            cls, bot: toof.ToofBot, user: discord.User,
            all_pics: ToofPics = ToofPics()):
        """Returns a menu for the given user by referencing the
        database.
        """

        if not all_pics:
            all_pics = await ToofPics.from_db(bot)

        if bot.user == user:
            usr_pics = sorted(all_pics)
        else:
            query = f"SELECT * FROM pics WHERE user_id = {user.id}"
            async with bot.db.execute(query) as cursor:
                usr_pics = sorted([
                    ToofPic(row[1], row[2], row[3], row[4])
                    async for row in cursor
                ])
        usr_pics = ToofPics(usr_pics)

        return cls(usr_pics, all_pics, user)

    @property
    def cur_pics(self) -> list[ToofPic]:
        """Return the list that relates to the current page."""
        return [pic for pic in self.pics if pic.rarity == self.page]

    @property
    def cur_content(self):
        """The current content for the menu."""
        if self.page == "overview" or self.cur_pics:
            return None
        return f"You don't have any {self.page} ToofPics!"
        
    @property
    def cur_embed(self):
        """The current embed of the menu."""
        if self.page == "overview":
            return self.__overview
        if self.cur_pics:
            return self.cur_pics[self.index].embed
        return None

    @property
    def page(self):
        """The current page of the menu."""
        return self.__page

    @page.setter
    def page(self, new_page: str | ToofPicRarity):
        """Sets the page and handles changing other attributes."""
        if isinstance(new_page, str):
            new_page = ToofPicRarity.get(new_page)
        if new_page != self.page:
            self.__index = 0
        self.__page = new_page

    @property
    def index(self):
        """The index of the current pic on the menu."""
        return self.__index

    @index.setter
    def index(self, new_index: int):
        """Changes the index of the current pic."""
        try:
            self.__index = new_index % len(self.cur_pics)
        except ZeroDivisionError:
            self.__index = 0

    @staticmethod
    def __get_overview_embed(
        usr_pics: ToofPics, all_pics: ToofPics,
        user: discord.User) -> discord.Embed | None:
        """Return an embed summarizing the collection. Returns none if the
        user has no pictures.
        """
        
        def summarize(rarity: ToofPicRarity) -> str:
            if rarity == "overview":
                num_usr = len(usr_pics)
                num_all = len(all_pics)
                description = f"\n**TOTAL:** {num_usr} of {num_all} pics "
            else:
                num_usr = len(usr_pics[rarity])
                num_all = len(all_pics[rarity])
                description = f"{num_usr} of {num_all} {rarity} pics "
            percent = num_usr / num_all * 100

            if num_usr == num_all:
                description += f"(💯)\n"
            else:
                description += f"({percent:.1f}%)\n"

            return description

        embed = discord.Embed(
            color=(
                discord.Color.gold() if len(usr_pics) == len(all_pics)
                else discord.Color.blurple()),
            description="")
        if user:
            embed.set_author(
                name=f"{user.name}'s Collection Overview:",
                icon_url=user.avatar.url)

        for rarity in ToofPicRarity.list() + [ToofPicRarity.overview]:
            embed.description += f"{rarity.emoji} {summarize(rarity)}"

        return embed
                
                
class CollectionSelect(discord.ui.Select):
    """Drop down menu to select the page for Toof pic collection."""

    def __init__(self, collection: Collection, *args, **kwargs):
        
        options = [
            discord.SelectOption(
                label=rarity.name.capitalize(),
                value=rarity.name,
                description=rarity.description,
                emoji=rarity.emoji,
                default=(collection.page == rarity)
            ) for rarity in [ToofPicRarity.overview] + ToofPicRarity.list()
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
    """Changes the current Toof Pic on the message. Must be constructed
    with either the previous() or next() class methods.
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
                collection.page != "overview"
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

    def __init__(self, bot: toof.ToofBot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    @discord.app_commands.command(
        name="roll",
        description="Get a random ToofPic.")
    @discord.app_commands.checks.cooldown(1, 5)
    async def pic_roll(self, interaction: discord.Interaction):
        """Selects a rarity based on chance, opens that a file of that
        rarity, and sends it.
        """

        all_pics = await ToofPics.from_db(self.bot)
        pic = all_pics.get_random()
        
        pic.date = datetime.now().strftime("%H:%M %m/%d/%Y")

        await interaction.response.send_message(embed=pic.embed)

        collection = await Collection.from_db(
            self.bot, interaction.user, all_pics)
        if pic not in collection.pics:
            query = f"""
                INSERT INTO pics
                VALUES (
                    {interaction.user.id}, '{pic.id}', '{pic.name}',
                    '{pic.link}', '{pic.date}')"""
            await self.bot.db.execute(query)
            await self.bot.db.commit()

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

        if random.randint(1, 3) != 3:
            await interaction.response.send_message(
                "you failed.", ephemeral=True)
            return

        all_pics = await ToofPics.from_db(self.bot)
        user_collection = await Collection.from_db(
            self.bot, interaction.user, all_pics)
        target_collection = await Collection.from_db(
            self.bot, target, all_pics)
        
        try:
            pic = target_collection.pics.get_random()
        except IndexError:
            await interaction.response.send_message(
                f"{target.mention} doesn't have any pics to steal !", ephemeral=True)
            return

        if pic not in user_collection.pics:
            
            date = datetime.now().strftime("%H:%M %m/%d/%Y")
            query = f"""
                UPDATE pics
                SET
                    user_id = {interaction.user.id},
                    date = '{date}'
                WHERE
                    user_id = {target.id} AND
                    pic_id = '{pic.id}'"""
            await self.bot.db.execute(query)
            await self.bot.db.commit()

            await interaction.response.send_message(
                f"{interaction.user.mention} stole a {pic.id} from {target.mention} !",
                embed=pic.embed)
        else:
            await interaction.response.send_message(
                f"u tried to steal a {pic.id} from {target.mention}, but u already hav 1!",
                embed=pic.embed,
                ephemeral=True)

    @discord.app_commands.command(
        name="collection",
        description="See what Toof pics you've collected.")
    async def pic_collection(self, interaction: discord.Interaction):
        """Allows users to see their collection of pics."""

        collection = await Collection.from_db(self.bot, interaction.user)
        
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


class ToofPicsCog(commands.Cog):
    """Cog which contains commands to interact with the Toof Pics
    extension.
    """

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot

    async def cog_load(self):
        self.bot.tree.add_command(
            discord.app_commands.ContextMenu(
                name="Check Collection",
                callback=self.collection_context_callback))
        self.bot.tree.add_command(
            PicCommandGroup(
                bot=self.bot,
                name="pic",
                description="Commands relating to ToofPics.",
                guild_only=True))

    async def collection_context_callback(
            self, interaction: discord.Interaction,
            member: discord.Member):
        """Returns an embed summarizing the user's collection."""

        collection = await Collection.from_db(self.bot, member)

        await interaction.response.send_message(
            content=f"{member.name} hasznt found any ToofPics :(" if not collection.pics else None,
            embed=collection.cur_embed if collection.pics else None,
            ephemeral=True)
    
    @discord.app_commands.command(
        name="picadd",
        description="Add a new Toof pic with a given image link.")
    @discord.app_commands.describe(
        rarity="The rarity of the new ToofPic.",
        link="A link to the picture.")
    @discord.app_commands.choices(rarity=[
        discord.app_commands.Choice(name="Common", value="C"),
        discord.app_commands.Choice(name="Rare", value="R"),
        discord.app_commands.Choice(name="Legendary", value="L")])
    @discord.app_commands.check(lambda i: i.user.id == 243845903146811393)
    async def pic_add(
            self, interaction: discord.Interaction,
            rarity: discord.app_commands.Choice[str], name: str, link: str):
        """Adds a new pic to the database, only usable by me."""

        all_pics = await ToofPics.from_db(self.bot)
        id = f"{rarity.value}{(len(all_pics)+1):03d}"
        date = datetime.now().strftime("%H:%M %m/%d/%Y")

        pic = ToofPic(id, name, link, date)

        query = f"""
            INSERT INTO pics 
            VALUES (0, '{id}', '{name}', '{link}', '{date}')"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            content="pic added:",
            embed=pic.embed,
            ephemeral=True)

    @pic_add.error
    async def pic_add_error(
            self, interaction: discord.Interaction, 
            error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.CheckFailure):
            await interaction.response.send_message(
                "u cant do that!", ephemeral=True)


async def setup(bot: toof.ToofBot):
    await bot.add_cog(ToofPicsCog(bot))
    