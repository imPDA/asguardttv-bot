import discord.ui
from discord.ext import commands
from discord import app_commands, SelectOption
from discord_argparse import ArgumentConverter, OptionalArgument
from discord.components import ComponentType, Button, ButtonStyle
from discord.types.components import ButtonComponent
# from discord.types import Message as MessagePayload
from discord.enums import MessageType
from views.set_trigger import Buttons
from discord.ui import Modal
from discord import Interaction, Object
from datetime import datetime
from typing import List

from clients.triggered_bot import Trigger, TriggeredBot
from database import TriggerNotFoundError


class CommandsTrigger(commands.Cog):
    """Description."""  # TODO

    def __init__(self, bot: TriggeredBot):
        self.bot: TriggeredBot = bot

    @app_commands.command(name='trigger')
    @app_commands.guilds(*[Object(id=922919845450903573), Object(id=699083894179495940), Object(id=806207945494364182)])
    @commands.has_permissions(administrator=True)
    async def trigger(self, interaction: Interaction, trigger_name: str):
        """Slash command to add/change trigger."""
        try:
            trigger = self.bot.db.get_trigger(guild_id=interaction.guild_id, trigger_name=trigger_name)
        except TriggerNotFoundError:
            trigger = None
        await interaction.response.send_modal(ModalSetTrigger(trigger_name=trigger_name, bot=self.bot, trigger=trigger))

    @trigger.autocomplete('trigger_name')
    async def trigger_name_autocomplete(
            self,
            interaction: Interaction,
            current: str
    ) -> List[app_commands.Choice[str]]:
        triggers = [trigger.name for trigger in self.bot.db.get_triggers(guild_id=interaction.guild_id) if current in trigger.name]
        return [app_commands.Choice(name=trigger, value=trigger) for trigger in triggers]

    @app_commands.command(name='list')
    @app_commands.guilds(*[Object(id=922919845450903573), Object(id=699083894179495940)])
    @commands.has_permissions(administrator=True)
    async def list(self, interaction: Interaction):
        """Slash command to print out list of triggers."""

        embed = discord.Embed(
            title=f'Триггеры гильдии {interaction.guild.name}',
            description='\n'.join(f'{i + 1}) **{trigger.name}**\n'
                                  f'Паттерн = `{trigger.pattern}`\n'
                                  f'Сообщ. = {trigger.msg}\n'
                                  f'Эмодзи = {trigger.emoji}\n'
                                  f'Режим = `{trigger.mode}`\n' for i, trigger in
                                  enumerate(self.bot.db.get_triggers(guild_id=interaction.guild_id))),
            timestamp=datetime.now(),
            colour=discord.Colour.default()
        )
        await interaction.response.send_message(embed=embed)


class ModalSetTrigger(Modal):
    """Description."""  # TODO

    def __init__(self, trigger_name: str, bot: commands.Bot, trigger: Trigger | None):
        title = f'Редактирование триггера {trigger_name}' if trigger else f'Добавление триггера {trigger_name}'  # TODO kinda no good
        super().__init__(title=title)

        self.bot = bot
        self.trigger_name = trigger_name

        if trigger:
            self.pattern.default, self.msg.default, self.emoji.default, self.mode.default = \
                trigger.dict_parameters.values()

    pattern = discord.ui.TextInput(
        label='Паттерн',
        style=discord.TextStyle.short,
        placeholder='Например: ".*доброе.*утро.*"',
    )

    msg = discord.ui.TextInput(
        label='Ответное сообщение',
        style=discord.TextStyle.long,
        placeholder='Например: "Доброе утро!"',
        required=False
    )

    emoji = discord.ui.TextInput(
        label='Эмодзи под сообщением',
        style=discord.TextStyle.short,
        placeholder='Например: "<:sunrise:>"',
        required=False
    )

    mode = discord.ui.TextInput(
        label='Режим',
        style=discord.TextStyle.short,
        placeholder='Например: "3" (сообщение и эмодзи)',
    )

    async def on_submit(self, interaction: Interaction) -> None:
        # TODO add function 1
        guild_id = interaction.guild.id
        self.bot.db.set_trigger(
            guild_id=guild_id,
            trigger=Trigger(
                name=self.trigger_name,
                pattern=self.pattern.value,
                msg=self.msg.value,
                emoji=self.emoji.value,
                mode=self.mode.value
            )
        )

        embed = discord.Embed(
            title=self.title,
            description=f'**{self.pattern.label}** `{self.pattern}`\n'
                        f'**{self.msg.label}** {self.msg}\n'
                        f'**{self.emoji.label}** {self.emoji}\n'
                        f'**{self.mode.label}** `{self.mode}`\n',
            timestamp=datetime.now(),
            colour=discord.Colour.default()
        )

        if self.bot.db.get_trigger(guild_id=guild_id,
                                   trigger_name=self.trigger_name) is not None:  # TODO advanced check!
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message('Something went wrong...')
        # TODO add function 1
