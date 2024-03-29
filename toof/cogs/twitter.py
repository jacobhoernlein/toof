"""Extension that includes twitter functionality. Used to provide a
stream of tweets into a channel, now just randomly tweets messages from
the server.
"""

import os
from random import randint

import discord
from discord.ext.commands import Cog
from tweepy.asynchronous import AsyncClient

import toof


class TwitterCog(Cog):

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
        self.tp = AsyncClient(
            consumer_key=os.getenv('TWEEPYAPITOKEN'),
            consumer_secret=os.getenv('TWEEPYAPISECRET'),
            access_token=os.getenv('TWEEPYACCESS'),
            access_token_secret=os.getenv('TWEEPYACCESSSECRET'))

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        if (msg.author == self.bot.user
            or randint(1, 4096) != 69
            or not msg.content):
            
            return
        
        name = msg.author.display_name
        content = msg.content
        if len(content) > (234 - len(name)):
            content = f"{content[0:(231 - len(name))]}..."
        
        response = await self.tp.create_tweet(text=f'"{content}" - {name}')
        url = f"https://twitter.com/ToofBot/status/{response.data['id']}"
        
        await msg.reply(url)


async def setup(bot: toof.ToofBot):
    await bot.add_cog(TwitterCog(bot))
    