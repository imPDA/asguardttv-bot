import inspect
from dataclasses import dataclass, field
from typing import Optional

import discord.ui
from discord.ext import commands
from discord import Game, Intents

import database
from database import BotDatabase
import re
import enum


@enum.unique
class ResponseMode(enum.Enum):
    OFF = 0
    MSG_ONLY = 1
    EMOJI_ONLY = 2
    ALL = 3


class BotStatus(enum.Enum):
    WORKING = enum.auto()
    BEING_CONFIGURED = enum.auto()


class ConfigStep(enum.Enum):
    NONE = enum.auto()
    ENTER_PATTERN = enum.auto()
    ENTER_MSG = enum.auto()
    ENTER_EMOJI = enum.auto()
    ENTER_MODE = enum.auto()
    END = enum.auto()


@dataclass
class Trigger:
    name: str
    pattern: str = None
    msg: str = None
    emoji: str = None
    mode: ResponseMode = ResponseMode.OFF

    def __post_init__(self):
        # if self.msg:
        #     self.mode = ResponseMode(self.mode.value + ResponseMode.MSG_ONLY.value)
        # if self.emoji:
        #     self.mode = ResponseMode(self.mode.value + ResponseMode.EMOJI_ONLY.value)
        pass

    @classmethod
    def from_database(cls, name: str, trigger: dict):
        return cls(name=name,
                   pattern=trigger['pattern'],
                   msg=trigger.get('msg'),
                   emoji=trigger.get('emoji'),
                   mode=ResponseMode(trigger['mode'])
                   )

    def serialize(self):
        return {
            self.name: self.serialize_parameters()
        }

    def serialize_parameters(self):
        return {
            'pattern': self.pattern,
            'msg': self.msg,
            'emoji': self.emoji,
            'mode': self.mode.value
        }


class Confirm(discord.ui.View):  # TODO split from here
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Cancelling', ephemeral=True)
        self.value = False
        self.stop()


class TriggeredBot(commands.Bot):
    """Custom Discord bot."""

    def __init__(self, command_prefix, intents: Intents, db: BotDatabase):
        super().__init__(
            command_prefix=commands.when_mentioned_or(command_prefix),
            intents=intents,
        )  # TODO description, help_command
        self._db: BotDatabase = db
        self._status = BotStatus.WORKING
        self._configure_step = ConfigStep.NONE
        self._new_trigger: Trigger = Trigger(name='')
        self._configure_msg = None
        self._configure_ctx = None

    def start_configuration(self, name, ctx):
        self._status = BotStatus.BEING_CONFIGURED
        self._configure_step = ConfigStep.ENTER_PATTERN
        self._new_trigger.name = name
        self._configure_ctx = ctx

    @property
    def db(self):
        return self._db

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        # await self.change_presence(activity=Game(name=f'{self.command_prefix}'))

    async def on_message(self, message):
        if message.author == self.user:
            return

        if self._status == BotStatus.BEING_CONFIGURED and message.channel == self._configure_ctx.channel \
                and message.author == self._configure_ctx.author:
            match self._configure_step:
                case ConfigStep.ENTER_PATTERN:
                    # print(message.content)
                    self._new_trigger.pattern = message.content
                    self._configure_step = ConfigStep.ENTER_MSG
                    await message.channel.send('Введите сообщение:')
                case ConfigStep.ENTER_MSG:
                    # print(message.content)
                    self._new_trigger.msg = message.content
                    self._configure_step = ConfigStep.ENTER_EMOJI
                    await message.channel.send('Введите эмодзи:')
                case ConfigStep.ENTER_EMOJI:
                    # print(message.content)
                    self._new_trigger.emoji = message.content
                    self._configure_step = ConfigStep.ENTER_MODE
                    await message.channel.send('Введите режим:')
                case ConfigStep.ENTER_MODE:
                    # print(message.content)
                    self._configure_step = ConfigStep.NONE
                    self._status = BotStatus.WORKING
                    self._new_trigger.mode = ResponseMode(int(message.content))
                    self._db.set_trigger(guild_id=message.guild.id, name_of_trigger=self._new_trigger.name,
                                         trigger_data=self._new_trigger.serialize_parameters())
                    await message.channel.send(f'\nИмя: {self._new_trigger.name}'
                                               f'\nПаттерн: {self._new_trigger.pattern}'
                                               f'\nОтветное сообщение: {self._new_trigger.msg}'
                                               f'\nЭмодзи: {self._new_trigger.emoji}'
                                               f'\nРежим: {self._new_trigger.mode}'
                                               )
            return

        if message.content.startswith('!'):  # TODO change to latest discord.py
            await self.process_commands(message)
            return

        try:
            triggers = self._db.get_triggers(message.guild.id)
        except database.NoGuildFoundError:
            print(f'There are no triggers in guild {message.guild.name}')  # TODO logging

        for name, data in triggers.items():
            if re.match(data['pattern'], message.content.lower()):
                match ResponseMode(data['mode']):
                    case ResponseMode.OFF:
                        pass
                    case ResponseMode.MSG_ONLY:
                        await message.channel.send(data['msg'])
                    case ResponseMode.EMOJI_ONLY:
                        await message.add_reaction(data['emoji'])
                    case ResponseMode.ALL:
                        await message.channel.send(data['msg'])
                        await message.add_reaction(data['emoji'])

# TODO name of guilds
# TODO local triggers to prevent from too frequent DB queries
