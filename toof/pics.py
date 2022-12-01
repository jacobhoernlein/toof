"""Contains classes relating to ToofPic functionality, but not relating
to Discord bot functionality (i.e. dataclasses).
"""

from dataclasses import dataclass
from datetime import datetime
import random

import discord


class PicRarity:
    """Class representing different ToofPic rarities."""

    def __init__(
            self, name: str, value: int, weight: float,
            emoji: discord.PartialEmoji, color: discord.Color,
            description: str):
        self.name = name
        self.value = value
        self.weight = weight
        self.emoji = emoji
        self.color = color
        self.description = description
        
    @classmethod
    @property
    def overview(cls):
        return cls(
            name="overview", value=0, weight=0,
            emoji=discord.PartialEmoji.from_str("🔎"),
            color=discord.Color.blurple(),
            description="Shows an overview of your entire ToofPic collection.")

    @classmethod
    @property
    def common(cls):
        return cls(
            name="common", value=1, weight=1,
            emoji=discord.PartialEmoji.from_str("🐶"),
            color=discord.Color.green(),
            description="Normal, run-of-the-mill ToofPics. (He is such a good boy).")

    @classmethod
    @property
    def rare(cls):
        return cls(
            name="rare", value=2, weight=0.1,
            emoji=discord.PartialEmoji.from_str("💎"),
            color=discord.Color.blue(),
            description="ToofPics of a bit higher quality. They are blue flavored.")

    @classmethod
    @property
    def legendary(cls):
        return cls(
            name="legendary", value=3, weight=0.01,
            emoji=discord.PartialEmoji.from_str("⭐"),
            color=discord.Color.gold(),
            description="The rarest, most awe-inspiring ToofPics money can buy.")

    @classmethod
    @property
    def unknown(cls):
        return cls(
            name="unknown", value=100, weight=0,
            emoji=discord.PartialEmoji.from_str("❓"),
            color=discord.Color.blurple(),
            description="IDK wut these r.")

    @classmethod
    def list(cls):
        """Returns a list of all rarities."""
        return [cls.common, cls.rare, cls.legendary]

    @classmethod
    def get(cls, page: str):
        match page[0].upper():
            case "O":
                return cls.overview
            case "C":
                return cls.common
            case "R":
                return cls.rare
            case "L":
                return cls.legendary
            case _:
                return cls.unknown

    def __eq__(self, other):
        if isinstance(other, PicRarity):
            return self.value == other.value
        elif isinstance(other, str):
            return self.name == other
        elif isinstance(other, int):
            return self.value == other
        else:
            raise TypeError(f"Equality not supported between Rarity and {other.__class__}")

    def __lt__(self, other):
        if isinstance(other, PicRarity):
            return self.value < other.value
        elif isinstance(other, int):
            return self.value < other
        else:
            raise TypeError(f"Less-Than not supported between Rarity and {other.__class__}")
        
    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Rarity.{self.name}: {self.value}>"


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
    def dt(self) -> datetime:
        return datetime.strptime(self.date, "%H:%M %m/%d/%Y")

    @dt.setter
    def dt(self, new_dt: datetime):
        self.date = new_dt.strftime("%H:%M %m/%d/%Y")

    @property
    def rarity(self) -> PicRarity:
        return PicRarity.get(self.id)
        
    @property
    def embed(self) -> discord.Embed:
        embed = discord.Embed(color=self.rarity.color)
        embed.set_author(name=f'{self.rarity.emoji} "{self.name}" • {self.id}')
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

    def __getitem__(self, key):
        if isinstance(key, str) or isinstance(key, PicRarity):
            return [pic for pic in self if pic.rarity == key]
        return super().__getitem__(key)
        
    def get_random(self) -> ToofPic:
        """Selects a random ToofPic from the list and returns it
        weighted by rarity. Raises IndexError if the list is empty.
        """

        rarities = PicRarity.list()

        while True:
            # Select a rarity from the list.
            rarity = random.choices(
                population=rarities,
                weights=[rarity.weight for rarity in rarities], 
                k=1)[0]
            
            try:
                return random.choice(self[rarity])
            # No pics for the chosen rarity. Remove and try again.
            except IndexError:
                rarities.remove(rarity)
                
    
class Collection:
    """Object representing a user's collection of ToofPics."""

    def __init__(
            self, usr_pics: ToofPics, all_pics: ToofPics = ToofPics(),
            user: discord.User = None):
        self.__overview = self.__get_overview_embed(usr_pics, all_pics, user)
        self.__index = 0
        self.__page = PicRarity.overview
        self.cur_pics = []
        self.pics = usr_pics

    @property
    def cur_content(self) -> str | None:
        """The current content for the menu."""
        if self.page == PicRarity.overview or self.cur_pics:
            return None
        return f"You don't have any {self.page} ToofPics!"
        
    @property
    def cur_embed(self) -> discord.Embed | None:
        """The current embed of the menu."""
        if self.page == PicRarity.overview:
            return self.__overview
        if self.cur_pics:
            return self.cur_pics[self.index].embed
        return None

    @property
    def page(self):
        """The current page of the menu."""
        return self.__page

    @page.setter
    def page(self, new_page: str | PicRarity):
        """Sets the page and handles changing other attributes."""
        if isinstance(new_page, str):
            new_page = PicRarity.get(new_page)
        elif not isinstance(new_page, PicRarity):
            raise TypeError(f"Cannot set Collection.page to {new_page.__class__}")
        if new_page != self.page:
            self.__index = 0
            self.__page = new_page
            self.cur_pics = self.pics[new_page]

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
        
        if not all_pics or user is None:
            return None

        embed = discord.Embed(
            color=(
                discord.Color.gold() if len(usr_pics) == len(all_pics)
                else discord.Color.blurple()),
            description="")
        embed.set_author(
            name=f"{user.name}'s Collection Overview:",
            icon_url=user.avatar.url)

        for rarity in PicRarity.list() + [PicRarity.overview]:
            if rarity == PicRarity.overview:
                num_usr = len(usr_pics)
                num_all = len(all_pics)
                embed.description += f"\n**TOTAL:** {num_usr} of {num_all} pics "
            else:
                num_usr = len(usr_pics[rarity])
                num_all = len(all_pics[rarity])
                embed.description += f"{rarity.emoji} {num_usr} of {num_all} {rarity} pics "
            try:
                percent = num_usr / num_all * 100
            except ZeroDivisionError:
                percent = 0

            if num_usr == num_all:
                embed.description += f"(💯)\n"
            else:
                embed.description += f"({percent:.1f}%)\n"

        return embed
