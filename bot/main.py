import os

import discord
from discord.ext import commands

import toof

# Initializes the bot using the ToofBot class
# with every intent enabled.
bot = toof.ToofBot(
    configfile='configs/server.json',
    cogfolder='cogs',

    command_prefix=("Toof, ", "toof, "),
    case_insensitive=True,
    strip_after_prefix=True,

    intents=discord.Intents.all(),
    
    max_messages=5000
)

# Logs successful startup
@bot.event
async def on_ready():
    bot.config.load()
    print("\
 _____             __   ___       _   \n\
/__   \___   ___  / _| / __\ ___ | |_ \n\
  / /\/ _ \ / _ \| |_ /__\/// _ \| __|\n\
 / / | (_) | (_) |  _/ \/  \ (_) | |_ \n\
 \/   \___/ \___/|_| \_____/\___/ \__|\n"
    )

# Reloads all extensions
@bot.command(hidden=True)
async def rollover(ctx: commands.Context):
    if ctx.author.id == 243845903146811393:
        await ctx.send("*rolls very hard*")
        await bot.toof_reload()
        await ctx.send("woof!")
    else:
        await ctx.send("*rolls*")

# Runs the bot with the token from the environment variable
bot.run(os.getenv('BOTTOKEN'))
