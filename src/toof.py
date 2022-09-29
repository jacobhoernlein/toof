"""
Establishes the config and bot classes,
run with --main or --dev arguments to bring
bot online.
"""

import asyncio
import os
import sqlite3
import sys

import random
from time import time
random.seed(time())

import discord
from discord.ext import commands


class ToofBot(commands.Bot):
    """Subclass of commands.Bot that includes neccessary configs and cleanups for toof."""

    def __init__(self, *args, **kwargs):
        """
        Takes in one required argument, the config file.
        Other args are the same as commands.Bot.
        """
        super().__init__(*args, **kwargs)

        self.db: sqlite3.Connection = sqlite3.connect('toof.sqlite')

        # Loads bot's extensions
        async def load_extensions():
            for filename in os.listdir('src/cogs'):
                if filename.endswith('.py'):
                    await self.load_extension(f'cogs.{filename[:-3]}')
        asyncio.run(load_extensions()) 

    async def on_ready(self):
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
        self.db.close()


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
