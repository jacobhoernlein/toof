"""Runs the bot with the token found in the environment files and
database provided with the first argument.
"""

import asyncio
import os
import sys

import random
from time import time
random.seed(time())

from . import ToofBot


os.system("clear")

bot = ToofBot(sys.argv[1])

bot.run(os.getenv("BOTTOKEN"))
asyncio.run(bot.db.close())
