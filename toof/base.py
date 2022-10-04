"""Establishes the base Bot and Cog class that other modules inherit
from.
"""

import aiosqlite

import discord
from discord.ext import commands


class Bot(commands.Bot):
    """Subclass of discord.ext.commands.Bot with an async sqlite3
    connection attribute.
    """

    def __init__(self):
        super().__init__(
            command_prefix="NO PREFIX",
            help_command=None,
            intents=discord.Intents.all(),
            max_messages=5000)

        self.db: aiosqlite.Connection = None
        
        
class Cog(commands.Cog):
    """Subclass of discord.ext.commands.Cog that contains a bot
    attribute.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
