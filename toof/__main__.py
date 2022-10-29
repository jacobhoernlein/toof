"""Runs the bot with the token found in the environment files and
database provided with the first argument.
"""

import os
import sys

import random
from time import time
random.seed(time())

from . import ToofBot


bot = ToofBot(sys.argv[1])
bot.run(os.getenv("BOTTOKEN"))
