"""Includes functionality for ToofPics"""

from dataclasses import dataclass
import json
import random

import discord

import toof


@dataclass
class ToofPic:
    """Representation of a ToofPic, including link, rarity, and ID"""

    link: str
    rarity: str
    id: str

    def embed(self) -> discord.Embed:
        """Returns a Discord Embed representation of the ToofPic."""

        if self.rarity == 'common':
            embed = discord.Embed(color=discord.Color.green()).set_image(url=self.link)
            embed.set_footer(text=f"🐶Common🐶 • ID: {self.id}")
        if self.rarity == 'rare':
            embed = discord.Embed(color=discord.Color.blue()).set_image(url=self.link)
            embed.set_footer(text=f"💎Rare💎 • ID: {self.id}")
        if self.rarity == 'legendary':
            embed = discord.Embed(color=discord.Color.gold()).set_image(url=self.link)
            embed.set_footer(text=f"⭐LEGENDARY⭐ • ID: {self.id}")

        return embed

    def __lt__(self, pic: "ToofPic"):
        return True if self.id < pic.id else False


class ToofPics(list[ToofPic]):
    """A list of ToofPics"""

    def commons(self) -> list[ToofPic]:
        """Returns a list of ToofPics that are common."""
        common_list = []
        for toof_pic in self:
            if toof_pic.rarity == 'common':
                common_list.append(toof_pic)
        return sorted(common_list)
    
    def rares(self) -> list[ToofPic]:
        """Returns a list of ToofPics that are rare."""
        rare_list = []
        for toof_pic in self:
            if toof_pic.rarity == 'rare':
                rare_list.append(toof_pic)
        return sorted(rare_list)

    def legendaries(self) -> list[ToofPic]:
        """Returns a list of ToofPics that are legendary."""
        legendary_list = []
        for toof_pic in self:
            if toof_pic.rarity == 'legendary':
                legendary_list.append(toof_pic)
        return sorted(legendary_list)

    def rand_common(self) -> ToofPic:
        """Returns a random common ToofPic."""  
        list = self.commons()
        if len(list) > 0:
            return random.choice(list)
        return None

    def rand_rare(self) -> ToofPic:
        """Returns a random rare ToofPic."""  
        list = self.rares()
        if len(list) > 0:
            return random.choice(list)
        return None

    def rand_legendary(self) -> ToofPic:
        """Returns a random legendary ToofPic."""  
        list = self.legendaries()
        if len(list) > 0:
            return random.choice(list)
        return None

    def find_pic(self, id: str) -> ToofPic:
        """Finds and returns a pic with the given ID if it is in the list."""
        for pic in self:
            if pic.id == id:
                return pic
        return None

    def overview(self, series: "ToofPics") -> discord.Embed:
        """
        Return a Discord embed summarizing the collection.
        The series is the collection of all pics used for comparison.
        """

        description = f"You have found {len(self)} of {len(series)} different pics.\n"
        description += f" • {len(self.commons())} / {len(series.commons())} commons 🐶\n"
        description += f" • {len(self.rares())} / {len(series.rares())} rares 💎\n"
        description += f" • {len(self.legendaries())} / {len(series.legendaries())} legendaries ⭐"

        embed = discord.Embed(
            color=discord.Color.greyple(),
            description=description
        )
        embed.set_author(name="Collection Overview:")

        return embed


class ToofPicCollectionSelect(discord.ui.Select):
    """Drop down menu to select the page for Toof pic collection."""

    def __init__(self, series: ToofPics, collection: ToofPics, page: str, *args, **kwargs):
        
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

        self.series = series
        self.collection = collection

    async def callback(self, interaction: discord.Interaction):
        page = self.values[0]
        
        if page == 'overview':
            embed = self.collection.overview(self.series)
            await interaction.response.edit_message(
                embed=embed,
                view=ToofPicCollectionView(self.series, self.collection, page)
            )
            return

        if page == 'common':
            pics = self.collection.commons()
        if page == 'rare':
            pics = self.collection.rares()
        if page == 'legendary':
            pics = self.collection.legendaries()

        if len(pics) > 0:
            content = None
            pic = pics[0]
            embed = pic.embed()
        else:
            content = f"You haven't found any {page} pics."
            pic = None
            embed = None

        await interaction.response.edit_message(
            content=content,
            embed=embed,
            view=ToofPicCollectionView(self.series, self.collection, page, pic)
        )


class ToofPicPreviousButton(discord.ui.Button):
    """Changes to the previous Toof pic in the collection."""

    def __init__(self, series: ToofPics, collection: ToofPics, page: str, curr_pic: ToofPic, *args, **kwargs):
        
        if page == 'common':
            pics = collection.commons()
        if page == 'rare':
            pics = collection.rares()
        if page == 'legendary':
            pics = collection.legendaries()
        
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

        self.series = series
        self.collection = collection
        self.page = page
        self.previous_pic = pics[index]

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.previous_pic.embed(),
            view=ToofPicCollectionView(
                series=self.series,
                collection=self.collection,
                page=self.page,
                pic=self.previous_pic
            )
        )


class ToofPicNextButton(discord.ui.Button):
    """Changes to next Toof pic in collection."""

    def __init__(self, series: ToofPics, collection: ToofPics, page: str, curr_pic: ToofPic, *args, **kwargs):
        
        if page == 'common':
            pics = collection.commons()
        if page == 'rare':
            pics = collection.rares()
        if page == 'legendary':
            pics = collection.legendaries()
        
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

        self.series = series
        self.collection = collection
        self.page = page
        self.next_pic = pics[index]

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.next_pic.embed(),
            view=ToofPicCollectionView(
                series=self.series,
                collection=self.collection,
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

    def __init__(self, series: ToofPics, collection: ToofPics, page: str, pic: ToofPic = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_item(ToofPicCollectionSelect(series, collection, page))

        if page != 'overview':
            self.add_item(ToofPicPreviousButton(series, collection, page, pic))
            self.add_item(ToofPicNextButton(series, collection, page, pic))
            self.add_item(ToofPicShareButton(pic))

    
async def setup(bot: toof.ToofBot):
    
    with open('configs/pics.json') as fp:
        pic_json = json.load(fp)

    toofpics = ToofPics()
    for pic_dict in pic_json:
        toofpic = ToofPic(
            link=pic_dict['link'],
            rarity=pic_dict['rarity'],
            id=pic_dict['id']
        )
        toofpics.append(toofpic)

    with open('configs/collections.json') as fp:
        collection_json: dict[str, list[str]] = json.load(fp)

    collections: dict[str, ToofPics] = {}
    for user_id, pic_ids in collection_json.items():
        collections[user_id] = ToofPics()
        for pic_id in pic_ids:
            collections[user_id].append(toofpics.find_pic(pic_id))

    @bot.tree.command(name="collection", description="See what Toof pics you've collected.")
    async def toof_pic_collection(interaction: discord.Interaction):
        """Allows users to see their collection of pics."""
        
        try:
            collection = collections[str(interaction.user.id)]
        except KeyError:
            await interaction.response.send_message(
                content="You don't have any Toof pics! Use /pic to find some.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=collection.overview(toofpics),
            view=ToofPicCollectionView(toofpics, collection, 'overview'),
            ephemeral=True
        )

    @bot.tree.command(name="pic", description="Get a random Toof pic.")
    async def toof_pic_command(interaction: discord.Interaction):
        """Selects a rarity based on chance, opens that a file of that rarity, and sends it."""

        user_id = str(interaction.user.id)

        num = random.randint(1, 256)
        if num >= 1 and num <= 3:
            pic = toofpics.rand_legendary()
        elif num >= 4 and num <= 25:
            pic = toofpics.rand_rare()
        else:
            pic = toofpics.rand_common()

        if user_id not in collections.keys():
            collections[user_id] = ToofPics()

        if pic not in collections[user_id]:
            collections[user_id].append(pic)

            with open('configs/collections.json') as fp:
                collection_json: dict[str, list[str]] = json.load(fp)

            if user_id not in collection_json.keys():
                collection_json[user_id] = []

            collection_json[user_id].append(pic.id)

            with open('configs/collections.json', 'w') as fp:
                json.dump(collection_json, fp, indent=4)
        
        await interaction.response.send_message(embed=pic.embed())

    @bot.tree.command(name="addtoofpic", description="Add a new toofpic with a given image link.")
    @discord.app_commands.guild_only()
    @discord.app_commands.describe(rarity="The rarity of the new ToofPic.", link="A link to the picture.")
    @discord.app_commands.choices(rarity=[
        discord.app_commands.Choice(name="Common", value='common'),
        discord.app_commands.Choice(name="Rare", value='rare'),
        discord.app_commands.Choice(name="Legendary", value='legendary')
    ])
    async def toof_pic_add(interaction: discord.Interaction, rarity: discord.app_commands.Choice[str], link: str):
        
        if interaction.user.id != 243845903146811393:
            await interaction.response.send_message(content="You can't do that!", ephemeral=True)
            return

        if rarity.value == 'common':
            id = f"C{(len(toofpics)+1):03d}"
        if rarity.value == 'rare':
            id = f"R{(len(toofpics)+1):03d}"
        if rarity.value == 'legendary':
            id = f"L{(len(toofpics)+1):03d}"

        toofpic = ToofPic(link, rarity.value, id)
        toofpics.append(toofpic)

        pic_dict = {
            'link': link,
            'rarity': rarity.value,
            'id': id
        }
        with open('configs/pics.json') as fp:
            pic_json = json.load(fp)
        pic_json.append(pic_dict)
        with open('configs/pics.json', 'w') as fp:
            json.dump(pic_json, fp, indent=4)
    
        await interaction.response.send_message(content="Pic Added:", embed=toofpic.embed(), ephemeral=True)
        