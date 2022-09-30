# toofbot

A Discord bot written in Python using the discord.py module.
Includes role menus and cute dog pics, and uses a sqlite3 database.

If you would like to test this yourself, make sure to add the proper tokens
for Discord and Tweepy into the proper environment variables.

Also, create a sqlite database with the following tables:
  - birthdays (user_id INTEGER, birthday TEXT)
  - pics (user_id INTEGER, pic_id TEXT, link TEXT)
  - roles (guild_id INTEGER, role_id INTEGER, emoji TEXT, description TEXT, type TEXT)
  - guilds (guild_id INTEGER, log_channel_id INTEGER, welcome_channel_id INTEGER, quotes_channel_id INTEGER, mod_role_id INTEGER, member_role_id INTEGER)

As of now, you must manually populate the values in the guilds table for the bot to run properly.
