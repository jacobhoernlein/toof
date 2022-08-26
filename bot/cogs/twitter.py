"""Twitter bot"""

import os
from random import randint

import discord
from discord.ext import commands
from tweepy.asynchronous import AsyncClient

import toof


class ToofTwitter(commands.Cog):

    def __init__(self, bot:toof.ToofBot):
        self.bot = bot
        
        self.tpclient = AsyncClient(
            consumer_key=os.getenv('TWEEPYAPITOKEN'),
            consumer_secret=os.getenv('TWEEPYAPISECRET'),
            access_token=os.getenv('TWEEPYACCESS'),
            access_token_secret=os.getenv('TWEEPYACCESSSECRET')
        )

    # Shiny messages
    @commands.Cog.listener()
    async def on_message(self, msg:discord.Message):
        if msg.channel in [
            self.bot.config.log_channel,
            self.bot.config.rules_channel,
            self.bot.config.welcome_channel,
            self.bot.config.quotes_channel
        ] \
        or msg.author == self.bot.user \
        or randint(1, 4096) != 69 \
        or not msg.content \
        or msg.guild != self.bot.config.server:
            return
        
        author_name = msg.author.display_name
        
        if len(msg.content) + len(author_name) <= 236:
            message = msg.content
        else:
            message = f"{msg.content[0:233-len(author_name)]}..."

        tweet_content = f"\"{message}\" -{author_name}"
        response = await self.tpclient.create_tweet(text=tweet_content)
        url = f"https://twitter.com/ToofBot/status/{response.data['id']}"
        await msg.reply(url)

        
async def setup(bot:toof.ToofBot):
    await bot.add_cog(ToofTwitter(bot))
