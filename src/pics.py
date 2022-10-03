"""Extension that implements the really cool Toof Pic system. Users get
a pic using /pic, then receive a random pic of a certain rarity. Then
they can see their entire collection using /pics.
"""

from dataclasses import dataclass
import random

import discord
from discord.ext import commands

import toof


@dataclass
class ToofPic:
    """A representation of a ToofPic. Contains an id, link, and
    embed.
    """

    id: str
    link: str
    
    @property
    def embed(self):
        """A Discord Embed representation of the ToofPic."""

        if self.id[0] == "C":
            embed = discord.Embed(color=discord.Color.green())
            embed.set_footer(text=f"🐶Common🐶 • ID: {self.id}")
        elif self.id[0] == "R":
            embed = discord.Embed(color=discord.Color.blue())
            embed.set_footer(text=f"💎Rare💎 • ID: {self.id}")
        elif self.id[0] == "L":
            embed = discord.Embed(color=discord.Color.gold())
            embed.set_footer(text=f"⭐LEGENDARY⭐ • ID: {self.id}")
        else:
            embed = discord.Embed(color=discord.Color.blurple())
            embed.set_footer(text=f"❓Unknown❓ • ID: {self.id}")

        embed.set_image(url=self.link)
        return embed

    def __lt__(self, pic: "ToofPic"):
        return True if int(self.id[1:]) < int(pic.id[1:]) else False


class ToofPics(list[ToofPic]):
    """A list of ToofPics, with methods relating to them."""

    def __getitem__(self, key):
        """Allows subscripting to access pics of different rarities by
        a string key. If item is not a string, uses default list
        behavior.
        """

        if not isinstance(key, str):
            return super().__getitem__(key)
        
        if key == "common":
            return self.commons
        if key == "rare":
            return self.rares
        if key == "legendary":
            return self.legendaries
        return ToofPics()

    @property
    def commons(self):
        """A list of ToofPics that are common from the list."""

        return ToofPics(sorted([pic for pic in self if pic.id[0] == 'C']))

    @property
    def rares(self):
        """A list of ToofPics that are rare from the list."""
       
        return ToofPics(sorted([pic for pic in self if pic.id[0] == 'R']))

    @property
    def legendaries(self):
        """A list of ToofPics that are legendary from the list."""
        
        return ToofPics(sorted([pic for pic in self if pic.id[0] == 'L']))
    
    def get_random(self) -> ToofPic | None:
        """Selects a random ToofPic from the list and returns it
        weighted by rarity. Returns None if the list is empty.
        """

        num = random.randint(1, 256)
        if num >= 1 and num <= 3:
            try:
                return random.choice(self.legendaries)
            except IndexError:
                num = 4
        if num >= 4 and num <= 25:
            try:
                return random.choice(self.rares)
            except IndexError:
                num = 26
        if num >= 26 and num <= 256:
            try:
                return random.choice(self.commons)
            except IndexError:
                return None

    def summarize(self, all_pics: "ToofPics") -> discord.Embed:
        """Return a Discord embed summarizing the list compared to
        all_pics.
        """

        description = f"You have found {len(self)} of {len(all_pics)} different pics.\n"
        description += f" • {len(self.commons)} / {len(all_pics.commons)} commons 🐶\n"
        description += f" • {len(self.rares)} / {len(all_pics.rares)} rares 💎\n"
        description += f" • {len(self.legendaries)} / {len(all_pics.legendaries)} legendaries ⭐"

        embed = discord.Embed(
            color=discord.Color.greyple(),
            description=description)
        embed.set_author(name="Collection Overview:")

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
                value="common",
                description="The ones you always see.",
                emoji="🐶",
                default=(page == "common")),
            discord.SelectOption(
                label="Rare Pics",
                value="rare",
                description="The ones you never see.",
                emoji="💎",
                default=(page == "rare")),
            discord.SelectOption(
                label="Legendary Pics",
                value="legendary",
                description="REAL???",
                emoji="⭐",
                default=(page == "legendary"))
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
            pic = None
            embed = self.user_collection.summarize(self.all_pics)
        elif pics:
            content = None
            pic = pics[0]
            embed = pic.embed
        else:
            content = f"u havent found any {page} pics!"
            pic = None
            embed = None
                
        await interaction.response.edit_message(
            content=content,
            embed=embed,
            view=ToofPicCollectionView(
                self.all_pics, self.user_collection, page, pic))


class ChangeToofPicButton(discord.ui.Button):
    """Changes the current Toof Pic on the message. Must be constructed
    with either the previous() or next() class methods.
    """

    all_pics: ToofPics
    user_collection: ToofPics
    page: str
    next_pic: ToofPic

    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

    @classmethod
    def previous(
            cls, all_pics: ToofPics, user_collection: ToofPics,
            page: str, curr_pic: ToofPic, *args, **kwargs):
        """Returns a button that changes the current pic to the
        previous one.
        """

        pics = user_collection[page]
        
        button = cls(disabled=(len(pics) < 2), emoji="⏪", *args, **kwargs)

        if len(pics) < 2:
            return button

        index = pics.index(curr_pic) - 1
        if index == -1:
            index = len(pics) - 1

        button.all_pics = all_pics
        button.user_collection = user_collection
        button.page = page
        button.next_pic = pics[index]

        return button

    @classmethod
    def next(
            cls, all_pics: ToofPics, user_collection: ToofPics,
            page: str, curr_pic: ToofPic, *args, **kwargs):
        """Returns a button that changes the current pic to the next
        one.
        """

        pics = user_collection[page]
        
        button = cls(disabled=(len(pics) < 2), emoji="⏩", *args, **kwargs)

        if len(pics) < 2:
            return button

        index = pics.index(curr_pic) + 1
        if index == len(pics):
            index = 0

        button.all_pics = all_pics
        button.user_collection = user_collection
        button.page = page
        button.next_pic = pics[index]

        return button

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.next_pic.embed,
            view=ToofPicCollectionView(
                all_pics=self.all_pics,
                user_collection=self.user_collection,
                page=self.page,
                pic=self.next_pic))


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
            page: str, pic: ToofPic = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_item(ToofPicCollectionSelect(
            all_pics, user_collection, page, row=0))

        if page != "overview":
            self.add_item(ChangeToofPicButton.previous(
                all_pics, user_collection, page, pic, row=1))
            self.add_item(ChangeToofPicButton.next(
                all_pics, user_collection, page, pic, row=1))
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
        else:
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
                embed=user_collection.summarize(all_pics),
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
        toofpic = ToofPic(id, link)

        query = f"INSERT INTO pics VALUES (0, '{id}', '{link}')"
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            content="pic added:",
            embed=toofpic.embed,
            ephemeral=True)
        

async def setup(bot: toof.ToofBot):
    await bot.add_cog(ToofPicsCog(bot))
