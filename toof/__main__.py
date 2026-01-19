"""Runs the bot with the token found in the environment files and
database provided with the first argument.
"""

import os
import sys

import random
from time import time
random.seed(time())

from dotenv import load_dotenv
load_dotenv()

from . import ToofBot


bot = ToofBot(sys.argv[1])
token = os.getenv("BOTTOKEN")

bot.run(token)
