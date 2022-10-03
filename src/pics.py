"""Extension that implements the really cool Toof Pic system. Users get
a pic using /pic, then receive a random pic of a certain rarity. Then
they can see their entire collection using /pics.
"""

from dataclasses import dataclass
from enum import Enum
import random

import discord
from discord.ext import commands

import toof


class ToofPicRarity(Enum):
    """Enum representing ToofPic Raritys."""

    common = 1
    rare = 2
    legendary = 3
    unknown = 100


@dataclass
class ToofPic:
    """A representation of a ToofPic. Contains an id, link, rarity,
    and embed.
    """

    id: str
    link: str
    
    @property
    def rarity(self) -> ToofPicRarity:
        if self.id.startswith("C"):
            return ToofPicRarity.common
        elif self.id.startswith("R"):
            return ToofPicRarity.rare
        elif self.id.startswith("L"):
            return ToofPicRarity.legendary
        else:
            return ToofPicRarity.unknown
        
    @property
    def embed(self) -> discord.Embed:
        if self.rarity == ToofPicRarity.common:
            embed = discord.Embed(color=discord.Color.green())
            embed.set_footer(text=f"🐶Common🐶 • ID: {self.id}")
        elif self.rarity == ToofPicRarity.rare:
            embed = discord.Embed(color=discord.Color.blue())
            embed.set_footer(text=f"💎Rare💎 • ID: {self.id}")
        elif self.rarity == ToofPicRarity.legendary:
            embed = discord.Embed(color=discord.Color.gold())
            embed.set_footer(text=f"⭐LEGENDARY⭐ • ID: {self.id}")
        else:
            embed = discord.Embed(color=discord.Color.blurple())
            embed.set_footer(text=f"ID: {self.id}")
    
        embed.set_image(url=self.link)
        return embed

    def __lt__(self, other: "ToofPic"):
        if self.rarity.value < other.rarity.value:
            return True
        if self.rarity.value > other.rarity.value:
            return False
        return True if self.id < other.id else False
    

class ToofPics(list[ToofPic]):
    """A list of ToofPics, with methods relating to them."""

    @property
    def commons(self) -> "ToofPics":
        """ToofPics from the object that are of common rarity."""

        return ToofPics(sorted([
            pic for pic in self
            if pic.rarity == ToofPicRarity.common]))

    @property
    def rares(self) -> "ToofPics":
        """ToofPics from the object that are of rare rarity."""
        
        return ToofPics(sorted([
            pic for pic in self
            if pic.rarity == ToofPicRarity.rare]))

    @property
    def legendaries(self) -> "ToofPics":
        """ToofPics from the object that are of legendary rarity."""
        
        return ToofPics(sorted([
            pic for pic in self
            if pic.rarity == ToofPicRarity.legendary]))
    
    @property
    def unkowns(self) -> "ToofPics":
        """ToofPics from the object that are of unknown rarity."""

        return ToofPics(sorted([
            pic for pic in self
            if pic.rarity == ToofPicRarity.unknown]))

    def __getitem__(self, key):
        if not isinstance(key, str):
            return super().__getitem__(key)
        
        try:
            return self.__getattribute__(key)
        except AttributeError:
            return ToofPics()
        
    def get_random(self) -> ToofPic | None:
        """Selects a random ToofPic from the list and returns it
        weighted by rarity. Returns None if the list is empty.
        """

        rarities = ["commons", "rares", "legendaries"]
        weights = [90, 9, 1]

        while True:
            rarity = random.choices(rarities, weights=weights, k=1)[0]
            index = rarities.index(rarity)

            try:
                return random.choice(self[rarity])
            except IndexError:
                try:
                    rarities.pop(index)
                    weights.pop(index)
                except IndexError:
                    return None

    
def collection_overview_embed(
        all_pics: ToofPics, user_collection: ToofPics,
        user: discord.User) -> discord.Embed:
    """Return an embed summarizing the user's collection."""

    num_usr_c = len(user_collection["commons"])
    num_usr_r = len(user_collection["rares"])
    num_usr_l = len(user_collection["legendaries"])
    usr_total = len(user_collection)

    num_all_c = len(all_pics["commons"])
    num_all_r = len(all_pics["rares"])
    num_all_l = len(all_pics["legendaries"])
    all_total = len(all_pics)

    percent_c = num_usr_c / num_all_c * 100
    percent_r = num_usr_r / num_all_r * 100
    percent_l = num_usr_l / num_all_l * 100
    percent_t = usr_total / all_total * 100

    if num_usr_c == num_all_c:
        description = f"\n 🐶 {num_usr_c} of {num_all_c} commons (💯)\n"
    else:
        description = f"\n 🐶 {num_usr_c} of {num_all_c} commons ({percent_c:.1f}%)\n"
    if num_usr_r == num_all_r:
        description += f" 💎 {num_usr_r} of {num_all_r} rares (💯)\n"
    else:
        description += f" 💎 {num_usr_r} of {num_all_r} rares ({percent_r:.1f}%)\n"
    if num_usr_l == num_all_l:
        description += f" ⭐ {num_usr_l} of {num_all_l} legendaries (💯)\n\n"
    else:
        description += f" ⭐ {num_usr_l} of {num_all_l} legendaries ({percent_l:.1f}%)\n\n"
    if usr_total == all_total:
        description += f"**TOTAL:** {usr_total} of {all_total} pics (💯)"
        color = discord.Color.gold()
    else:
        description += f"**TOTAL:** {usr_total} of {all_total} pics ({percent_t:.1f}%)"
        color = discord.Color.blurple()

    embed = discord.Embed(color=color, description=description)
    embed.set_author(
        name=f"{user.name}'s Collection Overview:",
        icon_url=user.avatar.url)

    return embed

class ToofPicCollectionSelect(discord.ui.Select):
    """Drop down menu to select the page for Toof pic collection."""

    def __init__(
            self, all_pics: ToofPics, user_collection: ToofPics,
            page: str, *args, **kwargs):
        
        options = [
            discord.SelectOption(
                label="Overview",
                value="overview",
                description="Shows an overview of your entire collection.",
                emoji="🔎",
                default=(page == "overview")),
            discord.SelectOption(
                label="Common Pics",
                value="commons",
                description="The ones you always see.",
                emoji="🐶",
                default=(page == "commons")),
            discord.SelectOption(
                label="Rare Pics",
                value="rares",
                description="The ones you never see.",
                emoji="💎",
                default=(page == "rares")),
            discord.SelectOption(
                label="Legendary Pics",
                value="legendaries",
                description="REAL???",
                emoji="⭐",
                default=(page == "legendaries"))
        ]
        
        super().__init__(options=options, *args, **kwargs)

        self.all_pics = all_pics
        self.user_collection = user_collection

    async def callback(self, interaction: discord.Interaction):
        """Changes the page of the menu to the selected option."""
        
        page = self.values[0]
        pics = self.user_collection[page]

        if page == "overview":
            content = None
            embed = collection_overview_embed(
                self.all_pics,
                self.user_collection,
                interaction.user
            )
        elif pics:
            content = None
            embed = pics[0].embed
        else:
            content = f"u havent found any {page} pics!"
            embed = None
                
        await interaction.response.edit_message(
            content=content,
            embed=embed,
            view=ToofPicCollectionView(
                self.all_pics, self.user_collection, page))


class ChangeToofPicButton(discord.ui.Button):
    """Changes the current Toof Pic on the message. Must be constructed
    with either the previous() or next() class methods.
    """

    def __init__(
            self, all_pics: ToofPics, user_collection: ToofPics,
            page: str, curr_index: int, *args, **kwargs):
        
        pics = user_collection[page]
        super().__init__(disabled=(len(pics) < 2), emoji="🔁", *args, **kwargs)

        self.all_pics = all_pics
        self.user_collection = user_collection
        self.page = page
        self.next_index = curr_index

    @classmethod
    def previous(
            cls, all_pics: ToofPics, user_collection: ToofPics,
            page: str, curr_index: int, *args, **kwargs):
        """Returns a button that changes the current pic to the
        previous one.
        """

        button = cls(all_pics, user_collection, page,
            curr_index, *args, **kwargs)
        
        button.emoji = "⏪"

        pics = user_collection[page]
        if len(pics) < 2:
            return button

        button.next_index = curr_index - 1
        if button.next_index == -1:
            button.next_index = len(pics) - 1

        return button

    @classmethod
    def next(
            cls, all_pics: ToofPics, user_collection: ToofPics,
            page: str, curr_index: int, *args, **kwargs):
        """Returns a button that changes the current pic to the next
        one.
        """

        button = cls(all_pics, user_collection, page,
            curr_index, *args, **kwargs)
        
        button.emoji = "⏩"

        pics = user_collection[page]
        if len(pics) < 2:
            return button

        button.next_index = curr_index + 1
        if button.next_index == len(pics):
            button.next_index = 0

        return button

    async def callback(self, interaction: discord.Interaction):
        """Edits the embed to show the next pic."""

        next_pic = self.user_collection[self.page][self.next_index]
        await interaction.response.edit_message(
            embed=next_pic.embed,
            view=ToofPicCollectionView(
                all_pics=self.all_pics,
                user_collection=self.user_collection,
                page=self.page,
                curr_index=self.next_index))


class ToofPicShareButton(discord.ui.Button):
    """Shares the currently selected pic into the interaction
    channel.
    """

    def __init__(self, pic: ToofPic, *args, **kwargs):
        super().__init__(
            style=discord.ButtonStyle.primary, label="Share",
            disabled=(pic is None), emoji="⤴️", *args, **kwargs)

        self.pic = pic

    async def callback(self, interaction: discord.Interaction):
        """Sends the selected Toof Pic into the interaction channel
        with a note that it belongs to the user.
        """

        embed = self.pic.embed
        embed.set_author(
            name=f"This pic was found by {interaction.user}:",
            icon_url=interaction.user.avatar.url)
        await interaction.channel.send(embed=embed)
        await interaction.response.defer()


class ToofPicCollectionView(discord.ui.View):
    """Contains a page select button, and buttons to navigate the
    page.
    """

    def __init__(
            self, all_pics: ToofPics, user_collection: ToofPics, 
            page: str, curr_index: int = 0, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_item(ToofPicCollectionSelect(
            all_pics, user_collection, page, row=0))

        if page == "overview":
            return

        self.add_item(ChangeToofPicButton.previous(
            all_pics, user_collection, page, curr_index, row=1))
        self.add_item(ChangeToofPicButton.next(
            all_pics, user_collection, page, curr_index, row=1))

        try:
            pic = user_collection[page][curr_index]
        except IndexError:
            pic = None

        self.add_item(ToofPicShareButton(pic, row=1))


class ToofPicsCog(commands.Cog):
    """Cog which contains commands to interact with the Toof Pics
    extension.
    """

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
    
    async def get_collection(self, user_id: int) -> ToofPics:
        """Get a list of ToofPics that belong to the given user_id. 0
        for all ToofPics.
        """

        query = f"SELECT * FROM pics WHERE user_id = {user_id}"
        async with self.bot.db.execute(query) as cursor:
            collection = ToofPics([
                ToofPic(row[1], row[2])
                async for row in cursor])
        return collection

    @discord.app_commands.command(
        name="pic",
        description="Get a random Toof pic.")
    async def pic_command(self, interaction: discord.Interaction):
        """Selects a rarity based on chance, opens that a file of that
        rarity, and sends it.
        """

        all_pics = await self.get_collection(0)
        pic = all_pics.get_random()
        
        if pic is None:
            await interaction.response.send_message(
                content="somethig went wrong :/",
                ephemeral=True)
            return
        
        await interaction.response.send_message(embed=pic.embed)

        user_collection = await self.get_collection(interaction.user.id)
        if pic not in user_collection:
            query = f"INSERT INTO pics VALUES ({interaction.user.id}, '{pic.id}', '{pic.link}')"
            await self.bot.db.execute(query)
            await self.bot.db.commit()

            
    @discord.app_commands.command(
        name="pics",
        description="See what Toof pics you've collected.")
    async def pics_command(self, interaction: discord.Interaction):
        """Allows users to see their collection of pics."""

        all_pics = await self.get_collection(0)
        user_collection = await self.get_collection(interaction.user.id)

        if user_collection:
            await interaction.response.send_message(
                embed=collection_overview_embed(
                    all_pics, user_collection, interaction.user),
                view=ToofPicCollectionView(
                    all_pics, user_collection, "overview"),
                ephemeral=True)
        else:
            await interaction.response.send_message(
                content="u dont have any Toof pics! use /pic to find sum.",
                ephemeral=True)

    @discord.app_commands.command(
        name="newpic",
        description="Add a new Toof pic with a given image link.")
    @discord.app_commands.describe(
        rarity="The rarity of the new ToofPic.",
        link="A link to the picture.")
    @discord.app_commands.choices(rarity=[
        discord.app_commands.Choice(name="Common", value="C"),
        discord.app_commands.Choice(name="Rare", value="R"),
        discord.app_commands.Choice(name="Legendary", value="L")])
    async def newpic_command(
            self, interaction: discord.Interaction,
            rarity: discord.app_commands.Choice[str], link: str):
        """Adds a new pic to the database, only usable by me."""

        if interaction.user.id != 243845903146811393:
            await interaction.response.send_message(
                content="woof !u cant do that!",
                ephemeral=True)
            return

        all_pics = await self.get_collection(0)
        id = f"{rarity.value}{(len(all_pics)+1):03d}"
        pic = ToofPic(id, link)

        query = f"INSERT INTO pics VALUES (0, '{id}', '{link}')"
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            content="pic added:",
            embed=pic.embed,
            ephemeral=True)
        

async def setup(bot: toof.ToofBot):
    await bot.add_cog(ToofPicsCog(bot))
