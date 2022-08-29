"""Cog that contains twitter functionality."""

import os
from random import randint

import discord
from discord.ext import commands
import tweepy

import toof


class ToofTwitter(commands.Cog):
    """Cog that contains Twitter functionality."""

    def __init__(self, bot: toof.ToofBot):
        self.bot = bot
        self.tpclient = tweepy.Client(
            consumer_key=os.getenv('TWEEPYAPITOKEN'),
            consumer_secret=os.getenv('TWEEPYAPISECRET'),
            access_token=os.getenv('TWEEPYACCESS'),
            access_token_secret=os.getenv('TWEEPYACCESSSECRET')
        )

    # Shiny messages
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author == self.bot.user \
        or randint(1, 4096) != 69 \
        or not msg.content:
            return
        
        author_name = msg.author.display_name
        
        message = f"{msg.content[0:(234 - (len(author_name)))]}..."

        tweet_content = f"\"{message}\" -{author_name}"
        response = self.tpclient.create_tweet(text=tweet_content)
        url = f"https://twitter.com/ToofBot/status/{response.data['id']}"
        await msg.reply(url)

    
async def setup(bot: toof.ToofBot):
    await bot.add_cog(ToofTwitter(bot))
