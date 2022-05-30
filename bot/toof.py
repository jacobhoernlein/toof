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
    

class QuotesConfig:
    """Class that includes a the quotes channel and list of message ids"""

    def __init__(self, bot:"ToofBot", config:dict):
        self.channel:discord.TextChannel = bot.get_channel(config['channels']['quotes']['id'])
        self.list:list[int] = config['channels']['quotes']['list']


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

        self.twitter:TwitterConfig = None
        self.quotes:QuotesConfig = None
        
        self.activities:list[discord.Activity] = None
        self.birthdays:dict = None

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
        self.twitter = TwitterConfig(self.__bot, config)
        self.quotes = QuotesConfig(self.__bot, config) 

        self.activities = []
        for name in config['activities']['watching']:
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=name
            )
            self.activities.append(activity)
        for name in config['activities']['listening']:
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name=name
            )
            self.activities.append(activity)
        for name in config['activities']['playing']:
            activity = discord.Activity(
                type=discord.ActivityType.playing,
                name=name
            )
            self.activities.append(activity)

        self.birthdays = {}
        for day in config['birthdays'].keys():
            self.birthdays[day] = config['birthdays'][day]

    def save(self):
        """Saves the configs to the config file file"""
        with open(self.__filename) as fp:
            config = json.load(fp)
        
        # config['server_id'] = self.server.id

        # config['roles']['mod'] = self.mod_role.id
        # config['roles']['mute'] = self.mute_role.id
        # config['roles']['member'] = self.member_role.id
        
        # config['channels']['log'] = self.log_channel.id
        # config['channels']['rules'] = self.rules_channel.id
        # config['channels']['welcome'] = self.welcome_channel.id
        # config['channels']['main'] = self.main_channel.id

        # config['channels']['twitter']['id'] = self.twitter.channel.id
        config['channels']['twitter']['latest'] = self.twitter.latest
        
        # config['channels']['quotes']['id'] = self.quotes.channel.id
        config['channels']['quotes']['list'] = self.quotes.list
        
        for activity in self.activities:
            # Adds new "watching" activities to the config
            if activity.type == discord.ActivityType.watching \
            and activity.name not in config['activities']['watching']:
                config['activities']['watching'].append(activity.name)

            # Adds new "listening" activities to the config
            elif activity.type == discord.ActivityType.listening \
            and activity.name not in config['activities']['listening']:
                config['activities']['listening'].append(activity.name)

            # Adds new "playing" activities to the config
            elif activity.type == discord.ActivityType.playing \
            and activity.name not in config['activities']['playing']:
                config['activities']['playing'].append(activity.name)
        
        for day in self.birthdays.keys():
            config['birthdays'][day] = self.birthdays[day]           

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
                