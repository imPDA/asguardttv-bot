from discord.ext import commands
from discord import Intents, Guild as DiscordGuild

from database import GuildDatabase
import re
from enums import ResponseMode


class TriggeredBot(commands.Bot):
    """Custom Discord bot."""

    def __init__(self, command_prefix, intents: Intents, db: GuildDatabase):
        super().__init__(
            command_prefix=commands.when_mentioned_or(command_prefix),
            intents=intents,
        )  # TODO description, help_command
        self._db: GuildDatabase = db

    @property
    def db(self) -> GuildDatabase:
        return self._db

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

    async def on_guild_join(self, guild: DiscordGuild):
        print(f'Joined {guild.name} (ID {guild.id})')  # TODO logging
        if guild.id not in self._db.guilds.keys():
            self._db.add_new_guild(guild=guild)

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('!'):  # TODO change to latest discord.py
            await self.process_commands(message)
            return

        triggers = self._db.guild(guild_id=message.guild.id).triggers.values()

        for trigger in triggers:
            if re.match(trigger.pattern, message.content.lower()):
                match trigger.mode:
                    case ResponseMode.OFF:
                        pass
                    case ResponseMode.MSG_ONLY:
                        await message.channel.send(trigger.msg)
                    case ResponseMode.EMOJI_ONLY:
                        await message.add_reaction(trigger.emoji)
                    case ResponseMode.ALL:
                        await message.channel.send(trigger.msg)
                        await message.add_reaction(trigger.emoji)
