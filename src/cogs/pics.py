"""
Extension that implements the really cool Toof Pic system. Users get
a pic using /pic, then receive a random pic of a certain rarity.
Then they can see their entire collection using /pics.
"""

from dataclasses import dataclass
import random

import discord
from discord.ext import commands

import toof


@dataclass
class ToofPic:
    """Representation of a ToofPic, including link, rarity, and ID"""

    id: str
    link: str
    
    def embed(self) -> discord.Embed:
        """Returns a Discord Embed representation of the ToofPic."""

        if self.id[0] == 'C':
            embed = discord.Embed(color=discord.Color.green()).set_image(url=self.link)
            embed.set_footer(text=f"🐶Common🐶 • ID: {self.id}")
        if self.id[0] == 'R':
            embed = discord.Embed(color=discord.Color.blue()).set_image(url=self.link)
            embed.set_footer(text=f"💎Rare💎 • ID: {self.id}")
        if self.id[0] == 'L':
            embed = discord.Embed(color=discord.Color.gold()).set_image(url=self.link)
            embed.set_footer(text=f"⭐LEGENDARY⭐ • ID: {self.id}")

        return embed

    def __lt__(self, pic: "ToofPic"):
        return True if int(self.id[1:]) < int(pic.id[1:]) else False


class ToofPics(list[ToofPic]):
    """A list of ToofPics, as well as methods relating."""

    def commons(self) -> "ToofPics":
        """Returns a list of ToofPics that are common from self."""

        return ToofPics(sorted([pic for pic in self if pic.id[0] == 'C']))
    
    def rares(self) -> "ToofPics":
        """Returns a list of ToofPics that are rare."""
       
        return ToofPics(sorted([pic for pic in self if pic.id[0] == 'R']))

    def legendaries(self) -> "ToofPics":
        """Returns a list of ToofPics that are legendary."""
        
        return ToofPics(sorted([pic for pic in self if pic.id[0] == 'L']))

    def overview(self, collection: "ToofPics") -> discord.Embed:
        """
        Return a Discord embed summarizing the collection.
        The series is the collection of all pics used for comparison.
        """

        description = f"You have found {len(collection)} of {len(self)} different pics.\n"
        description += f" • {len(collection.commons())} / {len(self.commons())} commons 🐶\n"
        description += f" • {len(collection.rares())} / {len(self.rares())} rares 💎\n"
        description += f" • {len(collection.legendaries())} / {len(self.legendaries())} legendaries ⭐"

        embed = discord.Embed(
            color=discord.Color.greyple(),
            description=description
        )
        embed.set_author(name="Collection Overview:")

        return embed


class ToofPicCollectionSelect(discord.ui.Select):
    """Drop down menu to select the page for Toof pic collection."""

    def __init__(self, all_pics: ToofPics, user_collection: ToofPics, page: str, *args, **kwargs):
        
        options = [
            discord.SelectOption(
                label="Overview",
                value='overview',
                description="Shows an overview of your entire collection.",
                emoji="🔎",
                default=(page == 'overview')
            ),
            discord.SelectOption(
                label="Common Pics",
                value='common',
                description="The ones you always see.",
                emoji="🐶",
                default=(page == 'common')
            ),
            discord.SelectOption(
                label="Rare Pics",
                value='rare',
                description="The ones you never see.",
                emoji="💎",
                default=(page == 'rare')
            ),
            discord.SelectOption(
                label="Legendary Pics",
                value='legendary',
                description="REAL???",
                emoji="⭐",
                default=(page == 'legendary')
            )
        ]
        
        super().__init__(
            options=options,
            row=0,
            *args, **kwargs
        )

        self.all_pics = all_pics
        self.user_collection = user_collection

    async def callback(self, interaction: discord.Interaction):
        page = self.values[0]
        
        if page == 'overview':
            embed = self.all_pics.overview(self.user_collection)
            await interaction.response.edit_message(
                embed=embed,
                view=ToofPicCollectionView(self.all_pics, self.user_collection, page)
            )
            return

        if page == 'common':
            pics = self.user_collection.commons()
        if page == 'rare':
            pics = self.user_collection.rares()
        if page == 'legendary':
            pics = self.user_collection.legendaries()

        if len(pics) > 0:
            content = None
            pic = pics[0]
            embed = pic.embed()
        else:
            content = f"u havent found any {page} pics!"
            pic = None
            embed = None

        await interaction.response.edit_message(
            content=content,
            embed=embed,
            view=ToofPicCollectionView(self.all_pics, self.user_collection, page, pic)
        )


class ToofPicPreviousButton(discord.ui.Button):
    """Changes to the previous Toof pic in the collection."""

    def __init__(self, all_pics: ToofPics, user_collection: ToofPics, page: str, curr_pic: ToofPic, *args, **kwargs):
        
        if page == 'common':
            pics = user_collection.commons()
        if page == 'rare':
            pics = user_collection.rares()
        if page == 'legendary':
            pics = user_collection.legendaries()
        
        super().__init__(
            disabled=(curr_pic is None or len(pics) < 2),
            emoji="⏪",
            row=1,
            *args, **kwargs
        )

        if curr_pic is None:
            return

        index = pics.index(curr_pic)
        index -= 1
        if index == -1:
            index = len(pics) - 1

        self.all_pics = all_pics
        self.user_collection = user_collection
        self.page = page
        self.previous_pic = pics[index]

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.previous_pic.embed(),
            view=ToofPicCollectionView(
                all_pics=self.all_pics,
                user_collection=self.user_collection,
                page=self.page,
                pic=self.previous_pic
            )
        )


class ToofPicNextButton(discord.ui.Button):
    """Changes to next Toof pic in collection."""

    def __init__(self, all_pics: ToofPics, user_collection: ToofPics, page: str, curr_pic: ToofPic, *args, **kwargs):
        
        if page == 'common':
            pics = user_collection.commons()
        if page == 'rare':
            pics = user_collection.rares()
        if page == 'legendary':
            pics = user_collection.legendaries()
        
        super().__init__(
            disabled=(curr_pic is None or len(pics) < 2),
            emoji="⏩",
            row=1,
            *args, **kwargs
        )

        if curr_pic is None:
            return

        index = pics.index(curr_pic)
        index += 1
        if index == len(pics):
            index = 0

        self.all_pics = all_pics
        self.user_collection = user_collection
        self.page = page
        self.next_pic = pics[index]

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.next_pic.embed(),
            view=ToofPicCollectionView(
                all_pics=self.all_pics,
                user_collection=self.user_collection,
                page=self.page,
                pic=self.next_pic
            )
        )


class ToofPicShareButton(discord.ui.Button):
    """Shares the currently selected pic into the interaction channel."""

    def __init__(self, pic: ToofPic, *args, **kwargs):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="Share",
            disabled=(pic is None),
            emoji="⤴️",
            row=1,
            *args, **kwargs
        )
        self.pic = pic

    async def callback(self, interaction: discord.Interaction):
        embed = self.pic.embed().set_author(
            name=f"This pic was found by {interaction.user}:",
            icon_url=interaction.user.avatar.url
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.defer()


class ToofPicCollectionView(discord.ui.View):
    """View containing a page select button, and buttons to navigate the page."""

    def __init__(self, all_pics: ToofPics, user_collection: ToofPics, page: str, pic: ToofPic = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_item(ToofPicCollectionSelect(all_pics, user_collection, page))

        if page != 'overview':
            self.add_item(ToofPicPreviousButton(all_pics, user_collection, page, pic))
            self.add_item(ToofPicNextButton(all_pics, user_collection, page, pic))
            self.add_item(ToofPicShareButton(pic))


class ToofPicsCog(commands.Cog):
    """Cog which contains commands to interact with the Toof Pics extension."""

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
    
    async def get_collection(self, user_id: int) -> ToofPics:
        """Get a list of ToofPics that belong to the given user_id. 0 for all ToofPics."""
        
        async with self.bot.db.execute(f'SELECT * FROM pics WHERE user_id = {user_id}') as cursor:
            collection = ToofPics([ToofPic(record[1], record[2]) async for record in cursor])
        return collection

    async def get_random_pic(self, user_id: int) -> ToofPic | None:
        """
        Selects a random ToofPic from the given user_id and returns it weighted by rarity.
        Returns none if there are no pictures.
        """

        user_collection = await self.get_collection(user_id)

        num = random.randint(1, 256)
        if num >= 1 and num <= 3:
            try:
                pic = random.choice(user_collection.legendaries())
            except IndexError:
                num = 4
        if num >= 4 and num <= 25:
            try:
                pic = random.choice(user_collection.rares())
            except IndexError:
                num = 26
        if num >= 26 and num <= 256:
            try:
                pic = random.choice(user_collection.commons())
            except IndexError:
                pic = None

        return pic

    @discord.app_commands.command(name="pic", description="Get a random Toof pic.")
    async def toof_pic_command(self, interaction: discord.Interaction):
        """Selects a rarity based on chance, opens that a file of that rarity, and sends it."""

        pic = await self.get_random_pic(0)

        if pic is None:
            await interaction.response.send_message("somethig went wrong :/", ephemeral=True)
        else:
            await interaction.response.send_message(embed=pic.embed())

        user_collection = await self.get_collection(interaction.user.id)
        if pic not in user_collection:
            await self.bot.db.execute(f'INSERT INTO pics VALUES ({interaction.user.id}, \'{pic.id}\', \'{pic.link}\')')
            await self.bot.db.commit()

            
    @discord.app_commands.command(name="pics", description="See what Toof pics you've collected.")
    async def toof_pic_collection(self, interaction: discord.Interaction):
        """Allows users to see their collection of pics."""

        all_pics = await self.get_collection(0)
        user_collection = await self.get_collection(interaction.user.id)

        if len(user_collection) == 0:
            await interaction.response.send_message(
                content="u dont have any Toof pics! use /pic to find sum.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=all_pics.overview(user_collection),
                view=ToofPicCollectionView(all_pics, user_collection, 'overview'),
                ephemeral=True
            )

    @discord.app_commands.command(name="newpic", description="Add a new Toof pic with a given image link.")
    @discord.app_commands.describe(rarity="The rarity of the new ToofPic.", link="A link to the picture.")
    @discord.app_commands.choices(rarity=[
        discord.app_commands.Choice(name="Common", value='C'),
        discord.app_commands.Choice(name="Rare", value='R'),
        discord.app_commands.Choice(name="Legendary", value='L')
    ])
    async def toof_pic_add(self, interaction: discord.Interaction, rarity: discord.app_commands.Choice[str], link: str):
        """Adds a new pic to the database, only usable by me."""

        if interaction.user.id != 243845903146811393:
            await interaction.response.send_message(content="woof !u cant do that!", ephemeral=True)
            return

        all_pics = await self.get_collection(0)
        id = f'{rarity.value}{(len(all_pics)+1):03d}'
        toofpic = ToofPic(id, link)

        await self.bot.db.execute(f'INSERT INTO pics VALUES (0, \'{id}\', \'{link}\')')
        await self.bot.db.commit()

        await interaction.response.send_message(content="pic added:", embed=toofpic.embed(), ephemeral=True)
        
async def setup(bot: toof.ToofBot):
    await bot.add_cog(ToofPicsCog(bot))
