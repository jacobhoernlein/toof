"""Submodule containing the cogs that will be added to a ToofBot."""

from .birthdays import BirthdayCog
from .misc import MiscCog
from .moderation import ModCog
from .pics import ToofPicsCog
from .quotes import QuotesCog
from .roles import RolesCog
from .twitter import TwitterCog
from .voice import VoiceCog
from .welcome import WelcomeCog

all_cogs = [
    BirthdayCog, MiscCog, ModCog,
    ToofPicsCog, QuotesCog, RolesCog,
    TwitterCog, VoiceCog, WelcomeCog
]
