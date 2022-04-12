from discord.ext import commands
from discord import Game, Intents, Object

import database
from database import RedisTriggeredBotDatabase
import re
from enums import ResponseMode
from datatypes import Trigger


class TriggeredBot(commands.Bot):
    """Custom Discord bot."""

    def __init__(self, command_prefix, intents: Intents, db: RedisTriggeredBotDatabase):
        super().__init__(
            command_prefix=commands.when_mentioned_or(command_prefix),
            intents=intents,
        )  # TODO description, help_command
        self._db: RedisTriggeredBotDatabase = db

    @property
    def db(self):
        return self._db

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

        guilds = [  # TODO-1 to .env  TODO-2 do i need it?
            Object(id='922919845450903573'),
            Object(id='699083894179495940'),
            Object(id='806207945494364182')
        ]

        for guild in guilds:
            await self.tree.sync(guild=guild)

    async def on_guild_join(self, guild):
        print(f'Joined {guild.id}')  # TODO logging
        await self.tree.sync(guild=Object(id=guild.id))

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('!'):  # TODO change to latest discord.py
            await self.process_commands(message)
            return

        try:
            triggers = self._db.get_triggers(message.guild.id)
        except database.GuildNotFoundError:
            print(f'There are no triggers in guild {message.guild.name}')  # TODO logging
            return

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

# TODO name of guilds
# TODO local triggers to prevent from too frequent DB queries
