"""
Establishes the bot class and main function.
"""

import asyncio
import os

import random
from time import time
random.seed(time())

import aiosqlite
import discord
from discord.ext import commands


class ToofBot(commands.Bot):
    """Subclass of commands.Bot that contains an aiosqlite connection."""

    db: aiosqlite.Connection

    async def on_ready(self):
        self.db = await aiosqlite.connect('toof.sqlite')
        
        for filename in os.listdir('src/cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')

        await self.tree.sync()
        print("""
 _____             __   ___       _   
/__   \___   ___  / _| / __\ ___ | |_ 
  / /\/ _ \ / _ \| |_ /__\/// _ \| __|
 / / | (_) | (_) |  _/ \/  \ (_) | |_ 
 \/   \___/ \___/|_| \_____/\___/ \__|
                     Running Toof v2.5"""
        )

    async def on_disconnect(self):
        await self.db.close()

    async def on_resumed(self):
        self.db = await aiosqlite.connect('toof.sqlite')
    
    
if __name__ == "__main__":
    
    bot = ToofBot(
        command_prefix="NO PREFIX",
        help_command=None,
        intents=discord.Intents.all(),
        max_messages=5000
    )

    bot.run(os.getenv('BOTTOKEN'))
    if bot.db.is_alive():
        asyncio.run(bot.db.close())
