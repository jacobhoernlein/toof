"""
Establishes the config and bot classes,
run with --main or --dev arguments to bring
bot online.
"""

import aiosqlite
import os
import sys

import random
from time import time
random.seed(time())

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


if __name__ == "__main__":
    
    if len(sys.argv) != 2 or sys.argv[1] not in ['--main', '-m', '--dev', '-d']:
        print("Choose an option:")
        print("   --main, -m: Main branch.")
        print("   --dev, -d : Dev branch.")
        exit()

    elif sys.argv[1] in ['--main', '-m']:
        token = os.getenv('BOTTOKEN')

    elif sys.argv[1] in ['--dev', '-d']:
        token = os.getenv('TESTBOTTOKEN')

    bot = ToofBot(
        command_prefix="NO PREFIX",
        help_command=None,
        intents=discord.Intents.all(),
        max_messages=5000
    )
    bot.run(token)
