"""Extension that includes twitter functionality. Used to provide a
stream of tweets into a channel, now just randomly tweets messages from
the server.
"""

import os
from random import randint

import discord
from discord.ext import commands
from tweepy import Client as TPClient

from .. import base


class TwitterCog(base.Cog):
    """Cog that contains Twitter functionality."""

    def __init__(self, bot: base.Bot):
        self.bot = bot
        self.tpclient = TPClient(
            consumer_key=os.getenv('TWEEPYAPITOKEN'),
            consumer_secret=os.getenv('TWEEPYAPISECRET'),
            access_token=os.getenv('TWEEPYACCESS'),
            access_token_secret=os.getenv('TWEEPYACCESSSECRET'))

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        """One in 4096 chance to create a tweet from the message
        content.
        """
        
        if (msg.author == self.bot.user
            or randint(1, 4096) != 69
            or not msg.content):
            return
        
        author_name = msg.author.display_name
        message = msg.content[0:(234 - (len(author_name)))]
        tweet_content = f"\"{message}\" - {author_name}"
        response = self.tpclient.create_tweet(text=tweet_content)
        url = f"https://twitter.com/ToofBot/status/{response.data['id']}"
        
        await msg.reply(url)
