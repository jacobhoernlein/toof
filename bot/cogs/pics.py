"""Includes functionality for ToofPics"""

import os
import random

from PIL import Image
import pillow_heif
import discord
from discord.ext import commands

import toof

class ToofPics(commands.Cog):
    """Commands having to do with Toof Pics"""

    def __init__(self, bot:commands.Bot):
        self.bot = bot
        
        self.toofpics = {
            'common': [],
            'rare': [],
            'legendary': []
        }

        for filename in os.listdir('attachments'):
            if 'l' in filename:
                self.toofpics['legendary'].append(f'attachments/{filename}')
            elif 'r' in filename:
                self.toofpics['rare'].append(f'attachments/{filename}')
            else:
                self.toofpics['common'].append(f'attachments/{filename}')

    # Sends a random picture of Toof
    @commands.group(aliases=["picture"])
    async def pic(self, ctx: commands.Context):
        """Sends a random toofpic"""
        if ctx.invoked_subcommand: 
            return
        
        if random.randint(1, 256) == 1:
            filename = random.choice(self.toofpics['legendary'])
            content = f"⭐ **LEGENDARY** ⭐ (#{filename[12:-4]})"
        elif random.randint(1, 32) == 1:
            filename = random.choice(self.toofpics['rare'])
            content = f"💎 *Rare* 💎 (#{filename[12:-4]})"
        else:
            filename = random.choice(self.toofpics['common'])
            content = f"🐶 Common 🐶 (#{filename[12:-4]})"
        
        with open(filename, 'rb') as fp:
            pic = discord.File(fp, filename=filename)
            await ctx.send(
                content=content,
                file=pic
            )

    # Adds a toofpic to the folder
    @pic.command(name="add", hidden=True)
    async def pic_add(self, ctx: commands.Context, rarity:str=None):
        """Adds a picture to toof pics folder"""
        if ctx.author.id != 243845903146811393:
            await ctx.message.add_reaction("❌")
            return

        if not ctx.message.attachments or rarity is None:
            await ctx.message.add_reaction("❓")
            return
        
        pic_count = len(self.toofpics['common']) + len(self.toofpics['rare']) + len(self.toofpics['legendary'])

        if rarity.lower() == "common":
            fileaddress = f'attachments/{pic_count + 1}.jpg'
            self.toofpics['common'].append(fileaddress)
        elif rarity.lower() == "rare":
            fileaddress = f'attachments/{pic_count + 1}r.jpg'
            self.toofpics['rare'].append(fileaddress)
        elif rarity.lower() == "legendary":
            fileaddress = f'attachments/{pic_count + 1}l.jpg'
            self.toofpics['legendary'].append(fileaddress)

        file:discord.Attachment = ctx.message.attachments[0]

        # No conversion necessary, saves directly
        if file.filename.lower().endswith('.jpg'):
            with open(fileaddress, 'wb') as fp:
                await file.save(fp)

            await ctx.message.add_reaction("👍")
        # Converts image from png to jpg, then saves it
        elif file.filename.lower().endswith('.png'):
            with open('temp.png', 'wb') as fp:
                await file.save(fp)

            png = Image.open('temp.png')
            jpg = png.convert('RGB')
            jpg.save(fileaddress)
            os.remove('temp.png')

            await ctx.message.add_reaction("👍")
        # Converts HEIC to jpg, then saves it
        elif file.filename.lower().endswith('.heic'):
            with open('temp.heic', 'wb') as fp:
                await file.save(fp)

            with open('temp.heic', 'rb') as fp:    
                heif_file = pillow_heif.open_heif(fp)
            image = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                'raw',
            )
            image.save(fileaddress)
            os.remove('temp.heic')

            await ctx.message.add_reaction("👍")
        # Can't convert other formats
        else:
            await ctx.message.add_reaction("👎")

def setup(bot:toof.ToofBot):
    bot.add_cog(ToofPics(bot))