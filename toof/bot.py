"""Establishes the bot class."""

import aiosqlite

from .base import Bot
from .cogs import all_cogs


class ToofBot(Bot):
    """Subclass of discord.ext.commands.Bot that contains an aiosqlite
    connection.
    """

    def __init__(self, dbname: str):
        super().__init__()
        self.dbname = dbname

    async def on_ready(self):
        """Connects to the database and loads cogs, as well as syncs
        the command tree.
        """

        self.db = await aiosqlite.connect(self.dbname)
        await self.db.execute("CREATE TABLE IF NOT EXISTS birthdays (user_id INTEGER, birthday TEXT)")
        await self.db.execute("CREATE TABLE IF NOT EXISTS roles (guild_id INTEGER, role_id INTEGER, emoji TEXT, description TEXT, type TEXT)")
        await self.db.execute("CREATE TABLE IF NOT EXISTS pics (user_id INTEGER, pic_id TEXT, link TEXT)")
        await self.db.execute("CREATE TABLE IF NOT EXISTS guilds (guild_id INTEGER, log_channel_id INTEGER, welcome_channel_id INTEGER, quotes_channel_id INTEGER, mod_role_id INTEGER, member_role_id INTEGER)")
        await self.db.commit()

        # Adds all the cogs to the bot, relying on the list set up in
        # the cogs package. Each cog is a callable object that requires
        # the bot to be passed to work.
        for cog in all_cogs:
            await self.add_cog(cog(self))
        await self.tree.sync()
        
        print("""
 _____             __   ___       _   
/__   \___   ___  / _| / __\ ___ | |_ 
  / /\/ _ \ / _ \| |_ /__\/// _ \| __|
 / / | (_) | (_) |  _/ \/  \ (_) | |_ 
 \/   \___/ \___/|_| \_____/\___/ \__|
                     Running Toof v2.6"""
        )
