from discord.ext import commands
from database import BotDatabase
import re


class TriggeredBot(commands.Bot):
    """Custom Discord bot."""

    def __init__(self, command_prefix, db: BotDatabase):
        super().__init__(command_prefix=command_prefix)
        self._db: BotDatabase = db

    @property
    def db(self):
        return self._db

    async def on_ready(self):
        print(f'We have logged in as {self.user}.')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith(self.command_prefix):
            await self.process_commands(message)
            return

        triggers = self._db.get_triggers(message.guild.id)
        for name, data in triggers.items():
            if re.match(data['pattern'], message.content.lower()):  # TODO FIX no pattern
                match data['mode']:
                    case 0:  # Nothing = Turned off
                        pass
                    case 1:  # Message in chat
                        await message.channel.send(data['msg'])
                    case 2:  # Emoji
                        await message.add_reaction(data['emoji'])
                    case 3:  # All together
                        await message.channel.send(data['msg'])
                        await message.add_reaction(data['emoji'])
                    case _:  # Default = Should never be used
                        pass

# TODO name of guilds
# TODO enum mode
# TODO local triggers to prevent from too frequent DB queries
