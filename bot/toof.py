"""
Establishes the config and bot classes,
run with --main or --dev arguments to bring
bot online.
"""

import os
import sys
import json
import asyncio

import discord
from discord.ext import commands
  

class Config:
    """Class that includes information on Roles and Channels of a discord.Guild"""

    def __init__(self, bot:"ToofBot", configfile:str):
        self.__bot:"ToofBot" = bot
        self.filename = configfile

        self.server:discord.Guild = None

        self.roles:list[discord.Role] = []

        self.log_channel:discord.TextChannel = None
        self.main_channel:discord.TextChannel = None
        self.quotes_channel:discord.TextChannel = None
        
        self.activities:list[discord.Activity] = [
            discord.Activity(
                type=discord.ActivityType.watching,
                name="the mailman"
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="you pee"
            ),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="bees"
            ),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="february face"
            ),
            discord.Activity(
                type=discord.ActivityType.playing,
                name="with a ball"
            )
        ]

    def load(self):
        """Loads the config from the config file"""
        
        with open(self.filename) as fp:
            config = json.load(fp)

        self.server = self.__bot.get_guild(config['server_id'])

        self.log_channel = self.__bot.get_channel(
            config['channels']['log']
        )
        self.main_channel = self.__bot.get_channel(
            config['channels']['main']
        )
        self.quotes_channel = self.__bot.get_channel(
            config['channels']['quotes']
        )

        for role_id in config['roles']:
            role = discord.utils.find(
                lambda r: r.id == role_id,
                self.server.roles  
            )
            self.roles.append(role)


class ToofBot(commands.Bot):
    """Subclass of commands.Bot that includes neccessary configs and cleanups"""

    def __init__(self, configfile:str, cogfolder:str, *args, **kwargs):
        """
        Takes in two required arguments, the config file and cog folder.
        The rest of the arguments are the same as its super
        """
        super().__init__(*args, **kwargs)
        self.config = Config(self, configfile)
        
        # Loads bot's extensions
        async def load_extensions():
            for filename in os.listdir(cogfolder):
                if filename.endswith('.py'):
                    await self.load_extension(f'{cogfolder}.{filename[:-3]}')
        asyncio.run(load_extensions()) 

    async def on_ready(self):
        self.config.load()
        await self.tree.sync()
        print("\
 _____             __   ___       _   \n\
/__   \___   ___  / _| / __\ ___ | |_ \n\
  / /\/ _ \ / _ \| |_ /__\/// _ \| __|\n\
 / / | (_) | (_) |  _/ \/  \ (_) | |_ \n\
 \/   \___/ \___/|_| \_____/\___/ \__|\n\
                      Running Toof v2."
        )


if __name__ == "__main__":
    
    if len(sys.argv) != 2 or sys.argv[1] not in ['--main', '-m', '--dev', '-d']:
        print("Choose an option:")
        print("   --main, -m: Main branch.")
        print("   --dev, -d : Dev branch.")

    elif sys.argv[1] in ['--main', '-m']:
        # Initializes the bot using the ToofBot class
        # with every intent enabled.
        bot = ToofBot(
            configfile='configs/main.json',
            cogfolder='cogs',

            command_prefix="NO PREFIX",
            help_command=None,
            intents=discord.Intents.all(),
            max_messages=5000
        )
        
        # Runs the bot with the token from the environment variable
        bot.run(os.getenv('BOTTOKEN'))

    elif sys.argv[1] in ['--dev', '-d']:
        # Initializes the bot using the ToofBot class
        # with every intent enabled.
        bot = ToofBot(
            configfile='configs/dev.json',
            cogfolder='cogs',

            command_prefix="NO PREFIX",
            help_command=None,
            intents=discord.Intents.all(),
            max_messages=5000
        )
        
        # Runs the bot with the token from the environment variable
        bot.run(os.getenv('TESTBOTTOKEN'))
