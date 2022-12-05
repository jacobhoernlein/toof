"""Extension that allows a credit system within the server,
allowing users to upvote and downvote others.
"""

import discord

import toof


class VoteUserContext(discord.app_commands.ContextMenu):
    
    def __init__(self, bot: toof.ToofBot, name: str):
        super().__init__(
            name=name.capitalize(),
            callback=self.callback)
        self.bot = bot

    async def callback(
            self, interaction: discord.Interaction,
            member: discord.Member):
        
        match self.name:
            case "Upvote":
                await self.bot.change_credit(member, 1)
                await interaction.response.send_message(
                    f"updooted {member.mention}!",
                    ephemeral=True)
            case "Downvote":
                await self.bot.change_credit(member, -1)
                await interaction.response.send_message(
                    f"downvoted {member.mention} !",
                    ephemeral=True)


async def setup(bot: toof.ToofBot):
    bot.tree.add_command(VoteUserContext(bot, "Upvote"))
    bot.tree.add_command(VoteUserContext(bot, "Downvote"))
