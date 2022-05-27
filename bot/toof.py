"""Module which contains the bot class"""

import os
import json

import discord
from discord.ext import commands


class ToofBot(commands.Bot):
    """Subclass of commands.Bot that includes neccessary configs and cleanups"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open('configs/server.json') as fp:
            self.serverconf = json.load(fp)

        with open('configs/twitter.json') as fp:
            self.tpconf = json.load(fp)

        with open('configs/quotes.json') as fp:
            self.quotes = json.load(fp)

        self.activities = [
            discord.Activity(
                type=discord.ActivityType.watching,
                name="the mailman"
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
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="you pee"
            )
        ]

    # Preps the bot by saving the last tweet and disconnecting from voice
    async def prep_close(self):
        """Saves the last Tweet and disconnects voice clients"""
        with open('configs/twitter.json', 'w') as fp:
            json.dump(self.tpconf, fp, indent=4)
        with open('configs/quotes.json', 'w') as fp:
            json.dump(self.quotes, fp, indent=4)
        for voice in self.voice_clients:
            await voice.disconnect()    

    # Cleans up then closes connection to Discord
    async def toof_shut_down(self):
        """Cleans up then closes connection to Discord"""
        await self.prep_close()
        await self.close()
        print("*dies*")

    # Cleans up then reloads all extensions
    async def toof_reload(self, cogfolder:str):
        """Reloads all extensions"""
        print("*rolls over*")
        await self.prep_close()

        for filename in os.listdir(cogfolder):
            if filename.endswith('.py'):
                cogname = f'{cogfolder}.{filename[:-3]}'
                print(f"Reloading: {cogname}")
                
                try:
                    self.unload_extension(cogname)
                except commands.ExtensionNotLoaded:
                    print(f"Could not unload {cogname}. Not loaded.")
                
                self.load_extension(cogname)
