from discord.ext import commands
from discord import app_commands, Interaction
from typing import List

from clients.triggered_bot import TriggeredBot
from errors import WrongChannel
from datatypes import Settings


class SlashSettings(commands.Cog):
    """Description."""  # TODO
    def __init__(self, bot: TriggeredBot):
        self.bot: TriggeredBot = bot
        super().__init__()

    set = app_commands.Group(
        name='set',
        description='...',
    )

    @set.command(name='channel_for_settings', description="Указать канал для настроек")
    @commands.has_permissions(administrator=True)
    async def set_channel(self, interaction: Interaction, channel: str):
        """Description."""  # TODO
        print(channel)
        self.bot.db.guild(guild_id=interaction.guild_id).settings = Settings(
            restricted=True,
            allowed_channel=channel
        )

    @set_channel.autocomplete('channel')
    async def trigger_name_autocomplete(
            self,
            interaction: Interaction,
            current: str
    ) -> List[app_commands.Choice[str]]:
        return [] if not current else [
            app_commands.Choice(name=channel.name, value=channel.name) for channel in interaction.guild.text_channels
            if current in channel.name
        ]

    @set_channel.error
    async def set_channel_error(self, ctx, error):
        print(error)
