"""Establishes the bot class."""

import asyncio
import datetime
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

    def run(self, token: str):
        super().run(token)
        asyncio.run(self.db.close())

    async def on_ready(self):
        self.db = await aiosqlite.connect(self.dbname)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS birthdays (
                user_id INTEGER, 
                birthday TEXT)""")
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                guild_id INTEGER,
                role_id INTEGER,
                emoji TEXT,
                description TEXT, 
                type TEXT)""")
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS pics (
                user_id INTEGER,
                pic_id TEXT,
                name TEXT,
                link TEXT,
                date TEXT)""")
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id INTEGER,
                log_channel_id INTEGER,
                welcome_channel_id INTEGER,
                quotes_channel_id INTEGER, 
                mod_role_id INTEGER, 
                member_role_id INTEGER)""")
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                thread_id INTEGER,
                user_id INTEGER)""")
        await self.db.commit()

        cur_path = os.path.dirname(__file__)
        cogs_dir = os.path.join(cur_path, "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                await self.load_extension(
                    name=f".cogs.{filename[:-3]}",
                    package="toof")

        await self.tree.sync()

        print("""
 _____             __   ___       _   
/__   \___   ___  / _| / __\ ___ | |_ 
  / /\/ _ \ / _ \| |_ /__\/// _ \| __|
 / / | (_) | (_) |  _/ \/  \ (_) | |_ 
 \/   \___/ \___/|_| \_____/\___/ \__|""")

    async def get_birthday(self, user: discord.User) -> datetime.datetime:
        """Get the given user's birthday by searching the database."""

        query = f"SELECT birthday FROM birthdays WHERE user_id = {user.id}"
        async with self.db.execute(query) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return datetime.datetime.strptime(row[0], "%m/%d/%Y")

    async def get_log_channel(self, guild: discord.Guild):
        """Get the log channel for the server."""

        query = f"SELECT log_channel_id FROM guilds WHERE guild_id = {guild.id}"
        async with self.db.execute(query) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return self.get_channel(row[0])

    async def get_mod_role(self, guild: discord.Guild):
        """Get the mod role of the server."""

        query = f"SELECT mod_role_id FROM guilds WHERE guild_id = {guild.id}"
        async with self.db.execute(query) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return discord.utils.find(lambda r: r.id == row[0], guild.roles)

    async def get_quotes_channel(self, guild: discord.Guild):
        """Get the quotes channel of the guild by searching the bot's
        database.
        """
            
        query = f"""
            SELECT quotes_channel_id 
            FROM guilds
            WHERE guild_id = {guild.id}"""
        async with self.db.execute(query) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return self.get_channel(row[0])
        
    async def get_member_role(self, guild: discord.Guild):
        """Get the member role for the guild."""

        query = f"""
            SELECT member_role_id
            FROM guilds
            WHERE guild_id = {guild.id}"""
        async with self.db.execute(query) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return discord.utils.find(lambda r: r.id == row[0], guild.roles)

    async def get_welcome_channel(self, guild: discord.Guild):
        """Gets the welcome channel of the given guild."""
        
        query = f"""
            SELECT welcome_channel_id
            FROM guilds
            WHERE guild_id = {guild.id}"""
        async with self.db.execute(query) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return self.get_channel(row[0])
        
    @property
    def toofping_emote(self):
        return discord.utils.find(lambda e: e.name == "toofping", self.emojis)
