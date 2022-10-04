"""Extension that implements the really cool Toof Pic system. Users get
a pic using /pic, then receive a random pic of a certain rarity. Then
they can see their entire collection using /pics.
"""

from dataclasses import dataclass
from enum import Enum
import random

import discord

from .. import base


class ToofPicRarity(Enum):
    """Enum representing ToofPic Raritys."""

    common = 1
    rare = 2
    legendary = 3
    unknown = 100

    def __lt__(self, other: "ToofPicRarity"):
        return True if self.value < other.value else False


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
    def embed(self):
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
        if self.rarity < other.rarity:
            return True
        if self.rarity > other.rarity:
            return False
        return True if self.id < other.id else False
    

class ToofPics(list[ToofPic]):
    """A list of ToofPics, with methods relating to them."""

    @property
    def commons(self):
        """ToofPics from the object that are of common rarity."""

        return ToofPics(sorted([
            pic for pic in self
            if pic.rarity == ToofPicRarity.common]))

    @property
    def rares(self):
        """ToofPics from the object that are of rare rarity."""
        
        return ToofPics(sorted([
            pic for pic in self
            if pic.rarity == ToofPicRarity.rare]))

    @property
    def legendaries(self):
        """ToofPics from the object that are of legendary rarity."""
        
        return ToofPics(sorted([
            pic for pic in self
            if pic.rarity == ToofPicRarity.legendary]))
    
    @property
    def unkowns(self):
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

    
def collection_embed(
        all_pics: ToofPics, usr_pics: ToofPics,
        user: discord.User) -> discord.Embed:
    """Return an embed summarizing the user's collection."""

    def summarize(page: str) -> str:
        if page == "pics":
            num_usr = len(usr_pics)
            num_all = len(all_pics)
        else:
            num_usr = len(usr_pics[page])
            num_all = len(all_pics[page])
        percent = num_usr / num_all * 100

        description = f"{num_usr} of {num_all} {page} "
        if num_usr == num_all:
            description += f"(💯)\n"
        else:
            description += f"({percent:.1f}%)\n"

        return description

    embed = discord.Embed()
    embed.set_author(
        name=f"{user.name}'s Collection Overview:",
        icon_url=user.avatar.url)

    embed.description = "🐶 " + summarize("commons")
    embed.description += "💎 " + summarize("rares")
    embed.description += "⭐ " + summarize("legendaries")
    embed.description += "\n**TOTAL:** " + summarize("pics")
    
    if len(usr_pics) == len(all_pics):
        embed.color = discord.Color.gold()
    
    return embed


class ToofPicCollectionSelect(discord.ui.Select):
    """Drop down menu to select the page for Toof pic collection."""

    def __init__(
            self, all_pics: ToofPics, usr_pics: ToofPics,
            page: str, *args, **kwargs):
        
        options = [
            discord.SelectOption(
                label="Overview",
                value="overview",
                description="Shows an overview of your entire ToofPic collection.",
                emoji="🔎",
                default=(page == "overview")),
            discord.SelectOption(
                label="Common Pics",
                value="commons",
                description="Normal, run-of-the-mill ToofPics. (He is such a good boy).",
                emoji="🐶",
                default=(page == "commons")),
            discord.SelectOption(
                label="Rare Pics",
                value="rares",
                description="ToofPics of a bit higher quality. They are blue flavored.",
                emoji="💎",
                default=(page == "rares")),
            discord.SelectOption(
                label="Legendary Pics",
                value="legendaries",
                description="The rarest, most awe-inspiring ToofPics money can buy.",
                emoji="⭐",
                default=(page == "legendaries"))
        ]
        
        super().__init__(options=options, *args, **kwargs)

        self.all_pics = all_pics
        self.usr_pics = usr_pics

    async def callback(self, interaction: discord.Interaction):
        """Changes the page of the menu to the selected option."""
        
        page = self.values[0]
        pics = self.usr_pics[page]

        if page == "overview":
            content = None
            embed = collection_embed(
                self.all_pics, self.usr_pics, interaction.user)
        elif pics:
            content = None
            embed = pics[0].embed
        else:
            content = f"u havent found any {page}!"
            embed = None
                
        await interaction.response.edit_message(
            content=content,
            embed=embed,
            view=ToofPicCollectionView(
                self.all_pics, self.usr_pics, page))


class ChangeToofPicButton(discord.ui.Button):
    """Changes the current Toof Pic on the message. Must be constructed
    with either the previous() or next() class methods.
    """

    def __init__(
            self, all_pics: ToofPics, usr_pics: ToofPics,
            page: str, curr_index: int, *args, **kwargs):
        
        last_index = len(usr_pics[page]) - 1
        super().__init__(disabled=(last_index < 1), *args, **kwargs)

        if self.emoji.name == "⏪":
            self.next_index = curr_index - 1
            if self.next_index < 0:
                self.next_index = last_index
        else:
            self.next_index = curr_index + 1
            if self.next_index > last_index:
                self.next_index = 0

        self.all_pics = all_pics
        self.usr_pics = usr_pics
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        """Edits the embed to show the next pic."""

        next_pic = self.usr_pics[self.page][self.next_index]
        await interaction.response.edit_message(
            embed=next_pic.embed,
            view=ToofPicCollectionView(
                all_pics=self.all_pics,
                usr_pics=self.usr_pics,
                page=self.page,
                curr_index=self.next_index))


class ToofPicShareButton(discord.ui.Button):
    """Shares the currently selected pic into the interaction
    channel.
    """

    def __init__(
            self, all_pics: ToofPic, usr_pics: ToofPics,
            page: str, curr_index: int, *args, **kwargs):
        
        if page == "overview":
            disabled = False
        elif usr_pics[page]:
            disabled = False
        else:
            disabled = True

        super().__init__(
            style=discord.ButtonStyle.primary, label="Share",
            disabled=disabled, emoji="⤴️", *args, **kwargs)

        self.all_pics = all_pics
        self.usr_pics = usr_pics
        self.page = page
        self.curr_index = curr_index

    async def callback(self, interaction: discord.Interaction):
        """Sends the selected Toof Pic into the interaction channel
        with a note that it belongs to the user.
        """

        if self.page == "overview":
            embed = collection_embed(
                self.all_pics, self.usr_pics, interaction.user)
        else:
            pic = self.usr_pics[self.page][self.curr_index]
            embed = pic.embed.set_author(
                name=f"This ToofPic was found by {interaction.user}:",
                icon_url=interaction.user.avatar.url)

        await interaction.channel.send(embed=embed)
        await interaction.response.defer()


class ToofPicCollectionView(discord.ui.View):
    """Contains a page select button, and buttons to navigate the
    page.
    """

    def __init__(
            self, all_pics: ToofPics, usr_pics: ToofPics, 
            page: str, curr_index: int = 0, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_item(ToofPicCollectionSelect(
            all_pics, usr_pics, page, row=0))
        self.add_item(ChangeToofPicButton(
            all_pics, usr_pics, page, curr_index, emoji="⏪", row=1))
        self.add_item(ChangeToofPicButton(
            all_pics, usr_pics, page, curr_index, emoji="⏩", row=1))
        self.add_item(ToofPicShareButton(
            all_pics, usr_pics, page, curr_index, row=1))


class ToofPicsCog(base.Cog):
    """Cog which contains commands to interact with the Toof Pics
    extension.
    """

    async def cog_load(self):
        self.bot.tree.add_command(
            discord.app_commands.ContextMenu(
                name="Check Collection",
                callback=self.collection_context_callback))
    
    async def get_collection(self, user_id: int) -> ToofPics:
        """Get a list of ToofPics that belong to the given user_id. 0
        for all ToofPics.
        """

        query = f"SELECT * FROM pics WHERE user_id = {user_id}"
        async with self.bot.db.execute(query) as cursor:
            pics = ToofPics([ToofPic(row[1], row[2]) async for row in cursor])
        return pics

    async def collection_context_callback(
            self, interaction: discord.Interaction,
            member: discord.Member):
        """Returns an embed summarizing the user's collection."""

        all_pics = await self.get_collection(0)

        if member == self.bot.user:
            usr_pics = all_pics
        else:
            usr_pics = await self.get_collection(member.id)

        if usr_pics:
            content = None
            embed = collection_embed(all_pics, usr_pics, member)
        else:
            content = f"{member.name} hasznt found any ToofPics :("
            embed = None

        await interaction.response.send_message(
            content=content, embed=embed, ephemeral=True)

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

        usr_pics = await self.get_collection(interaction.user.id)
        if pic not in usr_pics:
            query = f"INSERT INTO pics VALUES ({interaction.user.id}, '{pic.id}', '{pic.link}')"
            await self.bot.db.execute(query)
            await self.bot.db.commit()

    @discord.app_commands.command(
        name="pics",
        description="See what Toof pics you've collected.")
    async def pics_command(self, interaction: discord.Interaction):
        """Allows users to see their collection of pics."""

        all_pics = await self.get_collection(0)
        usr_pics = await self.get_collection(interaction.user.id)

        if usr_pics:
            await interaction.response.send_message(
                embed=collection_embed(
                    all_pics, usr_pics, interaction.user),
                view=ToofPicCollectionView(
                    all_pics, usr_pics, "overview"),
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
        