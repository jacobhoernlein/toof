"""Includes functionality for ToofPics"""

import os
import random

from PIL import Image
import pillow_heif
import discord

import toof


async def setup(bot:toof.ToofBot):
    toofpics = {
        'common': [],
        'rare': [],
        'legendary': []
    }

    for filename in os.listdir('attachments'):
        if 'l' in filename:
            toofpics['legendary'].append(f'attachments/{filename}')
        elif 'r' in filename:
            toofpics['rare'].append(f'attachments/{filename}')
        else:
            toofpics['common'].append(f'attachments/{filename}')

    # Command to get a random Toof Pic
    @bot.tree.command(name="pic", description="Get a random Toof Pic.")
    async def toof_pic(interaction:discord.Interaction):
        if random.randint(1, 256) == 1:
            filename = random.choice(toofpics['legendary'])
            content = f"⭐ **LEGENDARY** ⭐ (#{filename[12:-4]})"
        elif random.randint(1, 32) == 1:
            filename = random.choice(toofpics['rare'])
            content = f"💎 *Rare* 💎 (#{filename[12:-4]})"
        else:
            filename = random.choice(toofpics['common'])
            content = f"🐶 Common 🐶 (#{filename[12:-4]})"
        
        with open(filename, 'rb') as fp:
            pic = discord.File(fp, filename=filename)
            await interaction.response.send_message(
                content=content,
                file=pic
            )

    # Class handling Toof Pic adding
    class ToofPicMenu(discord.ui.View):
        def __init__(self, count:int, msg:discord.Message, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.count = count
            self.msg = msg

        # Handles converting and saving images to attachments folder
        async def save_image(self, fileaddress:str):
            file = self.msg.attachments[0]

            # No conversion necessary, saves directly
            if file.filename.lower().endswith('.jpg'):
                with open(fileaddress, 'wb') as fp:
                    await file.save(fp)

            # Converts image from png to jpg, then saves it
            elif file.filename.lower().endswith('.png'):
                with open('temp.png', 'wb') as fp:
                    await file.save(fp)

                png = Image.open('temp.png')
                jpg = png.convert('RGB')
                jpg.save(fileaddress)
                os.remove('temp.png')

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

        @discord.ui.button(label="Common", emoji="🐶")
        async def add_common(self, interaction:discord.Interaction, button:discord.Button):
            fileaddress = f'attachments/{self.count + 1}.jpg'
            try:
                await self.save_image(fileaddress)
            except:
                await interaction.response.edit_message(content="❌")
            else:
                toofpics['common'].append(fileaddress)
                await interaction.response.edit_message(content="✅")

        @discord.ui.button(label="Rare", emoji="💎")
        async def add_rare(self, interaction:discord.Interaction, button:discord.Button):
            fileaddress = f'attachments/{self.count + 1}r.jpg'
            try:
                await self.save_image(fileaddress)
            except:
                await interaction.response.edit_message(content="❌")
            else:
                toofpics['rare'].append(fileaddress)
                await interaction.response.edit_message(content="✅")

        @discord.ui.button(label="Legendary", emoji="⭐")
        async def add_legendary(self, interaction:discord.Interaction, button:discord.Button):
            fileaddress = f'attachments/{self.count + 1}l.jpg'
            try:
                await self.save_image(fileaddress)
            except:
                await interaction.response.edit_message(content="❌")
            else:
                toofpics['legendary'].append(fileaddress)
                await interaction.response.edit_message(content="✅")

    # Adds a Toof Pic to the dictionary. Only usable by Jacob
    @bot.tree.context_menu(name="Add Toofpic")
    @discord.app_commands.guild_only()
    async def add_toofpic(interaction:discord.Interaction, msg:discord.Message):
        if interaction.user.id != 243845903146811393:
            await interaction.response.send_message(content="❌", ephemeral=True)
            return

        if not msg.attachments:
            await interaction.response.send_message(content="❓", ephemeral=True)
            return

        count = len(toofpics['common']) + len(toofpics['rare']) + len(toofpics['legendary'])
        await interaction.response.send_message(view=ToofPicMenu(count, msg), ephemeral=True)
