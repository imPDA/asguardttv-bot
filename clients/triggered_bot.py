from pprint import pprint

from discord.ext import commands
from discord import Intents, Guild
from discord.channel import DMChannel

from database import LocalDatabase, RedisDatabase, MyRedisDatabase
import re
from enums import ResponseMode

from datatypes import Guild as DBGuild


class TriggeredBot(commands.Bot):
    """Custom Discord bot."""

    def __init__(self, command_prefix, intents: Intents, remote_database: MyRedisDatabase):
        super().__init__(
            command_prefix=commands.when_mentioned_or(command_prefix),
            intents=intents,
        )  # TODO description, help_command
        self.local_database = LocalDatabase.load_from_database(remote_database)
        self.remote_database: MyRedisDatabase = remote_database
        self.sets = self.remote_database.get('1')
        # print(self.sets)  # TODO DELETE B4 PRODUCTION
        # print(len(self.sets))  # TODO DELETE B4 PRODUCTION

    @property
    def db(self) -> LocalDatabase:
        """:class:`GuildLocalDatabase`: Database of this bot."""
        return self.local_database

    # @property
    # def sets(self) -> dict[str, str]:
    #     # """:class:`GuildLocalDatabase`: Database of this bot."""
    #     return self.sets
    #
    # @sets.setter
    # def sets(self, value):
    #     self._sets = value

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} (ID: {self.user.id})")    # TODO logging

    async def on_guild_join(self, guild: Guild):
        print(f"Joined {guild.name} (ID {guild.id})")  # TODO logging
        if guild.id not in self.db.guilds:
            self.db.guilds.update({guild.id: DBGuild(id=guild.id, name=guild.name)})

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('!'):  # TODO change to latest discord.py
            await self.process_commands(message)
            return

        if isinstance(message.channel, DMChannel):  # no messages in DM!
            return

        triggers = self.db.guilds[message.guild.id].triggers.values()

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

    def save_local_database(self) -> None:
        self.local_database.save_to_redis_db(self.remote_database)

# TODO add DB saving and hashing
