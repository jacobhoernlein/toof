"""Module which contains the bot class"""

import os
import json

import discord
from discord.ext import commands


class TwitterConfig:
    """Class that includes the Twitter channel and lastest Tweet ID"""

    def __init__(self, bot:"ToofBot", config:dict):
        self.channel:discord.TextChannel = bot.get_channel(config['channels']['twitter']['id'])
        self.latest:int = config['channels']['twitter']['latest']
    

class Config:
    """Class that includes information on Roles and Channels of a discord.Guild"""

    def __init__(self, bot:"ToofBot", configfile:str):
        self.__bot:"ToofBot" = bot
        self.__filename = configfile

        self.server:discord.Guild = None

        self.mod_role:discord.Role = None
        self.mute_role:discord.Role = None
        self.member_role:discord.Role = None

        self.log_channel:discord.TextChannel = None
        self.rules_channel:discord.TextChannel = None
        self.welcome_channel:discord.TextChannel = None
        self.main_channel:discord.TextChannel = None
        self.quotes_channel:discord.TextChannel = None

        self.twitter:TwitterConfig = None
        
        self.activities:list[discord.Activity] = None

    def load(self):
        """Loads the config from the config file"""
        with open(self.__filename) as fp:
            config = json.load(fp)

        self.server = self.__bot.get_guild(config['server_id'])

        self.mod_role = discord.utils.find(
            lambda r: r.id == config['roles']['mod'],
            self.server.roles
        )
        self.mute_role = discord.utils.find(
            lambda r: r.id == config['roles']['mute'],
            self.server.roles
        )
        self.member_role = discord.utils.find(
            lambda r: r.id == config['roles']['member'],
            self.server.roles
        )

        self.log_channel = self.__bot.get_channel(
            config['channels']['log']
        )
        self.rules_channel = self.__bot.get_channel(
            config['channels']['rules']
        )
        self.welcome_channel = self.__bot.get_channel(
            config['channels']['welcome']
        )
        self.main_channel = self.__bot.get_channel(
            config['channels']['main']
        )
        self.quotes_channel = self.__bot.get_channel(
            config['channels']['quotes']
        )
        self.twitter = TwitterConfig(self.__bot, config)
        
        self.activities = [
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
        
    def save(self):
        """Saves the configs to the config file file"""
        with open(self.__filename) as fp:
            config = json.load(fp)
        
        config['channels']['twitter']['latest'] = self.twitter.latest
        
        with open(self.__filename, 'w') as fp:
            json.dump(config, fp, indent=4)


class ToofBot(commands.Bot):
    """Subclass of commands.Bot that includes neccessary configs and cleanups"""

    def __init__(self, configfile:str, cogfolder:str, *args, **kwargs):
        """
        Takes in two required arguments, the config file and cog folder.
        The rest of the arguments are the same as its super
        """
        super().__init__(*args, **kwargs)

        self.config = Config(self, configfile)
        
        self.__cogfolder = cogfolder
        for filename in os.listdir(self.__cogfolder):
            if filename.endswith('.py'):
                self.load_extension(f'{self.__cogfolder}.{filename[:-3]}')
        
    # Preps the bot by saving the last tweet and disconnecting from voice
    async def prep_close(self):
        """Saves the last Tweet and disconnects voice clients"""
        self.config.save()
        for voice in self.voice_clients:
            await voice.disconnect()    

    # Cleans up then closes connection to Discord
    async def toof_shut_down(self):
        """Cleans up then closes connection to Discord"""
        await self.prep_close()
        await self.close()
        print("*dies*")

    # Cleans up then reloads all extensions and configs
    async def toof_reload(self):
        """Reloads all extensions"""
        print("*rolls over*")
        await self.prep_close()

        # Uloads loaded extensions
        loaded_extensions = []
        for extension in self.extensions:
            loaded_extensions.append(str(extension))
        for extension in loaded_extensions:
            self.unload_extension(extension)

        # Loads all extensions in the cogs folder
        for filename in os.listdir(self.__cogfolder):
            if filename.endswith('.py'):
                extension = f'{self.__cogfolder}.{filename[:-3]}'
                
                try:
                    self.load_extension(extension)
                except commands.NoEntryPointError:
                    print(f"No setup function for {extension}. Skipping")
                
        # Loads new configs if they've been added.
        self.config.load()
                