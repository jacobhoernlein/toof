"""
Establishes the config and bot classes,
run with --main or --dev arguments to bring
bot online.
"""

import os
import sys
import json
import asyncio

import random
from time import time
random.seed(time())

import discord
from discord.ext import commands


class ToofConfig:
    """Class that includes information on Roles and Channels of a discord.Guild."""

    def __init__(self, bot: "ToofBot", configfile: str):
        self.__bot: "ToofBot" = bot
        self.filename = configfile

        self.server: discord.Guild = None

        self.log_channel: discord.TextChannel = None
        self.welcome_channel: discord.TextChannel = None
        self.quotes_channel: discord.TextChannel = None
        
        self.mod_role: discord.Role = None
        self.member_role: discord.Role = None

    def load(self):
        """Loads the config from the config file"""
        
        with open(self.filename) as fp:
            config = json.load(fp)

        self.server = self.__bot.get_guild(config['server_id'])

        self.log_channel = self.__bot.get_channel(
            config['channels']['log']
        )
        self.welcome_channel = self.__bot.get_channel(
            config['channels']['welcome']
        )
        self.quotes_channel = self.__bot.get_channel(
            config['channels']['quotes']
        )

        self.mod_role = discord.utils.find(lambda r: r.id == config['roles']['mod'], self.server.roles)
        self.member_role = discord.utils.find(lambda r: r.id == config['roles']['member'], self.server.roles)
        

class ToofBot(commands.Bot):
    """Subclass of commands.Bot that includes neccessary configs and cleanups for toof."""

    def __init__(self, configfile:str, *args, **kwargs):
        """
        Takes in one required argument, the config file.
        Other args are the same as commands.Bot.
        """
        super().__init__(*args, **kwargs)
        self.config = ToofConfig(self, configfile)
        
        # Loads bot's extensions
        async def load_extensions():
            for filename in os.listdir('src/cogs'):
                if filename.endswith('.py'):
                    await self.load_extension(f'cogs.{filename[:-3]}')
        asyncio.run(load_extensions()) 

    async def on_ready(self):
        self.config.load()
        await self.tree.sync()

        print("""
 _____             __   ___       _   
/__   \___   ___  / _| / __\ ___ | |_ 
  / /\/ _ \ / _ \| |_ /__\/// _ \| __|
 / / | (_) | (_) |  _/ \/  \ (_) | |_ 
 \/   \___/ \___/|_| \_____/\___/ \__|
                     Running Toof v2.4"""
        )


if __name__ == "__main__":
    
    if len(sys.argv) != 2 or sys.argv[1] not in ['--main', '-m', '--dev', '-d']:
        print("Choose an option:")
        print("   --main, -m: Main branch.")
        print("   --dev, -d : Dev branch.")
        exit()

    elif sys.argv[1] in ['--main', '-m']:
        configfile = 'configs/main.json'
        token = os.getenv('BOTTOKEN')

    elif sys.argv[1] in ['--dev', '-d']:
        configfile = 'configs/dev.json'
        token = os.getenv('TESTBOTTOKEN')

    bot = ToofBot(
        configfile=configfile,
        command_prefix="NO PREFIX",
        help_command=None,
        intents=discord.Intents.all(),
        max_messages=5000
    )
    bot.run(token)
