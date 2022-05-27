import os

import discord
from discord.ext import commands

import toof

cogfolder = 'cogs'

# Initializes the bot using the ToofBot class
# with every intent enabled.
prefixes = "Toof, ", "toof, "
bot = toof.ToofBot(
    command_prefix=prefixes,
    case_insensitive=True,
    strip_after_prefix=True,
    intents=discord.Intents.all(),
    max_messages=5000
)

# Logs successful startup
@bot.event
async def on_ready():
    print("woof.")

# Reloads all extensions
@bot.command(hidden=True)
async def rollover(ctx: commands.Context):
    if ctx.author.id == 243845903146811393:
        await ctx.send("*rolls very hard*")
        await bot.toof_reload(cogfolder)
        await ctx.send("woof!")

# Loads all of the cogs
for filename in os.listdir(cogfolder):
    if filename.endswith('.py'):
        bot.load_extension(f'{cogfolder}.{filename[:-3]}')

# Runs the bot with the token from the environment variable
bot.run(os.getenv('BOTTOKEN'))
