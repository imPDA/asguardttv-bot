from discord.ext import commands
from discord import app_commands, Interaction, Embed, Colour, TextStyle
from discord.ui import Modal, TextInput
from datetime import datetime
from typing import List

from errors import WrongChannel
from clients.triggered_bot import TriggeredBot
from datatypes import Trigger
from database import TriggerNotFoundError


class SlashTrigger(commands.Cog):
    """Description."""  # TODO
    def __init__(self, bot: TriggeredBot):
        self.bot: TriggeredBot = bot

    @app_commands.command(name='trigger', description="Добавить новый триггер или изменить существующий")
    # @commands.has_permissions(administrator=True)
    async def trigger(self, interaction: Interaction, name: str):
        """Slash command to add or change trigger."""
        try:
            trigger = self.bot.db.guild(guild_id=interaction.guild_id).triggers[name]
        except KeyError:
            trigger = None
        await interaction.response.send_modal(ModalSetTrigger(trigger_name=name, bot=self.bot, trigger=trigger))

    @trigger.autocomplete('name')
    async def trigger_name_autocomplete(
            self,
            interaction: Interaction,
            current: str
    ) -> List[app_commands.Choice[str]]:
        return [app_commands.Choice(name=trigger.name, value=trigger.name) for trigger
                in self.bot.db.guild(guild_id=interaction.guild_id).triggers.values()
                if current in trigger.name]

    @app_commands.command(name='list', description="Список всех команд сервера")
    # @commands.has_permissions(administrator=True)
    async def list(self, interaction: Interaction):
        """Slash command to print out list of triggers."""
        embed = Embed(
            title=f"Триггеры гильдии {interaction.guild.name}",
            description="\n".join(
                f"**{i + 1}. {trigger.name}**\n"
                f"**Паттерн** `{trigger.pattern}`\n"
                f"**Сообщ.** {trigger.msg}\n"
                f"**Эмодзи** {trigger.emoji}\n"
                f"**Режим** `{trigger.mode}`\n" for i, trigger in
                enumerate(self.bot.db.guild(guild_id=interaction.guild_id).triggers.values())
            ),
            timestamp=datetime.now(),
            colour=Colour.default()
        )
        await interaction.response.send_message(embed=embed)

    @list.error
    async def list_error(self, ctx, error):
        print(error)


class ModalSetTrigger(Modal):  # TODO rework?
    """Description."""  # TODO
    def __init__(self, trigger_name: str, bot: TriggeredBot, trigger: Trigger | None):
        title = f'Редактирование триггера {trigger_name}' if trigger else f'Добавление триггера {trigger_name}'
        super().__init__(title=title)

        self.bot: TriggeredBot = bot
        self.trigger_name = trigger_name

        if trigger:
            self.pattern.default, self.msg.default, self.emoji.default, self.mode.default = \
                trigger.dict_parameters.values()

    pattern = TextInput(
        label='Паттерн',
        style=TextStyle.short,
        placeholder='Например: ".*доброе.*утро.*"',
    )

    msg = TextInput(
        label='Ответное сообщение',
        style=TextStyle.long,
        placeholder='Например: "Доброе утро!"',
        required=False
    )

    emoji = TextInput(
        label='Эмодзи под сообщением',
        style=TextStyle.short,
        placeholder='Например: "<:sunrise:>"',
        required=False
    )

    mode = TextInput(
        label='Режим',
        style=TextStyle.short,
        placeholder='Например: "3" (сообщение и эмодзи)',
    )

    async def on_submit(self, interaction: Interaction) -> None:
        # TODO add function 1
        self.bot.db.guild(guild_id=interaction.guild_id).triggers[self.trigger_name] = Trigger(
            name=self.trigger_name,
            pattern=self.pattern.value,
            msg=self.msg.value,
            emoji=self.emoji.value,
            mode=self.mode.value
        )

        embed = Embed(
            title=self.title,
            description=f'**{self.pattern.label}** `{self.pattern}`\n'
                        f'**{self.msg.label}** {self.msg}\n'
                        f'**{self.emoji.label}** {self.emoji}\n'
                        f'**{self.mode.label}** `{self.mode}`\n',
            timestamp=datetime.now(),
            colour=Colour.default()
        )

        # if self.bot.db.get_trigger(guild=interaction.guild,
        #                            name=self.trigger_name) is not None:  # TODO advanced check!
        await interaction.response.send_message(embed=embed)
        # else:
        #     await interaction.response.send_message('Something went wrong...')
        # # TODO add function 1
