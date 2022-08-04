"""Twitter bot"""

import os
from random import randint

import discord
from discord.ext import commands, tasks
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

    # # Starts loops
    # @commands.Cog.listener()
    # async def on_ready(self):
    #     self.check_tweets.start()

    # Sends a Tweet from Toof's account
    @commands.command(hidden=True)
    async def tweet(self, ctx:commands.Context, *, content:str):
        """Sends a Tweet from Toof's account. Only usable by Jacob"""
        if ctx.author.id == 243845903146811393:
            response = await self.tpclient.create_tweet(text=content)
            url = f"https://twitter.com/ToofBot/status/{response.data['id']}"
            await ctx.reply(url)

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
        or not msg.content:
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

    # # Checks Toof's Timeline and uploads new tweets to the Twitter channel
    # @tasks.loop(seconds=15)
    # async def check_tweets(self):
    #     """
    #     Checks the bot's Twitter timeline every 15 seconds and puts the new
    #     Tweets into the server's Twitter channel.
    #     """
    #     # Gets timeline using the Tweepy client established in __init__
    #     timeline = await self.tpclient.get_home_timeline(
    #         max_results=100, 
    #         since_id=self.bot.config.twitter.latest, 
    #         tweet_fields=['id','author_id'],
    #         expansions=['author_id']
    #     )
        
    #     if not timeline.data:
    #         return

    #     # Builds a dictionary of users from the timeline response
    #     users = {}
    #     for user in timeline.includes['users']:
    #         users[str(user.id)] = user
        
    #     # Print Tweets in reverse order
    #     for tweet in reversed(timeline.data):
    #         # Gets the user object corresponding to the tweet from the dictionary
    #         user = users[str(tweet.author_id)]
            
    #         # Formats the link and sends it to the server's twitter channel
    #         username = user.username
    #         url = f"https://twitter.com/{username}/status/{tweet.id}"
    #         await self.bot.config.twitter.channel.send(url)

    #         # # Likes the tweet if it isn't made by ToofBot
    #         # if username != "ToofBot":
    #         #     await self.tpclient.like(tweet.id)

    #     # Updates the config to make the newest_tweet match the timeline query
    #     # So future loops don't end up posting the same tweets
    #     self.bot.config.twitter.latest = int(timeline.meta['newest_id'])

            
def setup(bot:toof.ToofBot):
    bot.add_cog(ToofTwitter(bot))
