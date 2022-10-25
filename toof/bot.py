"""Establishes the bot class."""

import os

import aiosqlite
import discord
from discord.ext import commands


class ToofBot(commands.Bot):
    """Subclass of discord.ext.commands.Bot that contains an aiosqlite
    connection.
    """

    def __init__(self, dbname: str):
        super().__init__(
            command_prefix="NO PREFIX",
            help_command=None,
            intents=discord.Intents.all(),
            max_messages=5000)

        self.db: aiosqlite.Connection = None
        self.dbname = dbname

    async def load_extensions(self):

        cur_path = os.path.dirname(__file__)
        cogs_dir = os.path.join(cur_path, "cogs")

        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                await self.load_extension(f".cogs.{filename[:-3]}", package="toof")

    async def on_ready(self):
        """Connects to the database and loads cogs, as well as syncs
        the command tree.
        """

        self.db = await aiosqlite.connect(self.dbname)
        await self.db.execute("CREATE TABLE IF NOT EXISTS birthdays (user_id INTEGER, birthday TEXT)")
        await self.db.execute("CREATE TABLE IF NOT EXISTS roles (guild_id INTEGER, role_id INTEGER, emoji TEXT, description TEXT, type TEXT)")
        await self.db.execute("CREATE TABLE IF NOT EXISTS pics (user_id INTEGER, pic_id TEXT, name TEXT, link TEXT, date TEXT)")
        await self.db.execute("CREATE TABLE IF NOT EXISTS guilds (guild_id INTEGER, log_channel_id INTEGER, welcome_channel_id INTEGER, quotes_channel_id INTEGER, mod_role_id INTEGER, member_role_id INTEGER)")
        await self.db.commit()

        await self.load_extensions()
        await self.tree.sync()

        print("""
 _____             __   ___       _   
/__   \___   ___  / _| / __\ ___ | |_ 
  / /\/ _ \ / _ \| |_ /__\/// _ \| __|
 / / | (_) | (_) |  _/ \/  \ (_) | |_ 
 \/   \___/ \___/|_| \_____/\___/ \__|""")
