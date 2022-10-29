"""Includes config commands for different servers."""

import discord
from discord.ext.commands import Cog

import toof

from .moderation import ModLogConfig
from .quotes import QuotesChannelConfig
from .roles import RolesConfig
from .welcome import WelcomeChannelConfig


class ConfigCommandGroup(discord.app_commands.Group):
    """Command Group that contains configs for different Cogs."""

    def __init__(self, bot: toof.ToofBot):
        super().__init__(
            name="config",
            description="Configure Toof features for this server.",
            guild_only=True)
        self.add_command(ModLogConfig(bot))
        self.add_command(QuotesChannelConfig(bot))
        self.add_command(RolesConfig(bot))
        self.add_command(WelcomeChannelConfig(bot))


class CongfigCog(Cog):
    
    def __init__(self, bot: toof.ToofBot):
        bot.tree.add_command(ConfigCommandGroup(bot))
        self.bot = bot

    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        query =f"INSERT INTO guilds VALUES ({guild.id}, 0, 0, 0, 0, 0)"
        await self.bot.db.execute(query)
        await self.bot.db.commit()


async def setup(bot: toof.ToofBot):
    bot.tree.add_command(ConfigCommandGroup(bot))
