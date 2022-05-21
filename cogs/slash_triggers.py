import asyncio

import discord.ui
from discord.ext import commands
from discord import app_commands, Interaction, Embed, Colour, TextStyle
from discord.ui import Modal, TextInput, View, Button
from discord.app_commands.errors import MissingPermissions
from datetime import datetime
from typing import List, Optional

from clients.triggered_bot import TriggeredBot
from datatypes import Trigger


class SlashTriggers(commands.Cog):
    """Description."""  # TODO
    def __init__(self, bot: TriggeredBot):
        self.bot: TriggeredBot = bot

    triggers = app_commands.Group(
        name="triggers",
        description="...",
    )

    @triggers.command(name='set', description="Добавить новый триггер или изменить существующий")
    @app_commands.checks.has_permissions(administrator=True)
    async def set(self, interaction: Interaction, name: str):
        """
        Slash command to add or change trigger.

        :param interaction:
        :param name:
        :return:
        """
        try:
            trigger = self.bot.db.guilds[interaction.guild_id].triggers[name]
        except KeyError:
            trigger = None
        await interaction.response.send_modal(ModalSetTrigger(trigger_name=name, bot=self.bot, trigger=trigger))

    @triggers.command(name='list', description="Список всех триггеров сервера")
    @app_commands.checks.has_permissions(administrator=True)
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
                enumerate(self.bot.db.guilds[interaction.guild.id].triggers.values())
            ),
            timestamp=datetime.now(),
            colour=Colour.default()
        )

        await interaction.response.send_message(embed=embed)

    @triggers.command(name='delete', description="Удалить триггер")
    @app_commands.checks.has_permissions(administrator=True)
    async def delete(self, interaction: Interaction, name: str):
        """Slash command to delete trigger."""

        delete_button = Button(label="Удалить", style=discord.ButtonStyle.danger)
        abort_button = Button(label="Отменить", style=discord.ButtonStyle.primary)

        async def delete_callback(interaction: Interaction) -> None:
            try:
                self.bot.db.guilds[interaction.guild_id].triggers.pop(name)
                self.bot.save_local_database()
            except KeyError:
                await interaction.response.edit_message(content=f"Ошибка удаления (KeyError).", view=None, embed=None)
            else:
                await interaction.response.edit_message(content=f"Триггер {name} удалён!", view=None, embed=None)

        async def abort_callback(interaction: Interaction) -> None:
            await interaction.response.edit_message(content="Отменено.", view=None, embed=None)

        delete_button.callback = delete_callback
        abort_button.callback = abort_callback

        view = View()
        view.add_item(delete_button)
        view.add_item(abort_button)

        trigger = self.bot.db.guilds[interaction.guild.id].triggers[name]
        embed = Embed(
            title=f"Удалить триггер {trigger.name}?",
            description=
                f"**Паттерн** `{trigger.pattern}`\n"
                f"**Сообщ.** {trigger.msg}\n"
                f"**Эмодзи** {trigger.emoji}\n"
                f"**Режим** `{trigger.mode}`\n",
            timestamp=datetime.now(),
            colour=Colour.default()
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @set.autocomplete('name')
    @delete.autocomplete('name')
    async def trigger_name_autocomplete(
            self,
            interaction: Interaction,
            current: str
    ) -> List[app_commands.Choice[str]]:
        return [app_commands.Choice(name=trigger.name, value=trigger.name) for trigger
                in self.bot.db.guilds[interaction.guild_id].triggers.values()
                if current in trigger.name]

    @delete.error
    async def delete_error(self, interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("Недостаточно прав для использования команды", ephemeral=True)
        else:
            print(error)

    @set.error
    async def set_error(self, interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("Недостаточно прав для использования команды", ephemeral=True)
        else:
            print(error)

    @list.error
    async def list_error(self, interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("Недостаточно прав для использования команды", ephemeral=True)
        else:
            print(error)


class ModalSetTrigger(Modal):
    """
    Yes, it is Description. TODO
    """

    def __init__(self, trigger_name: str, bot: TriggeredBot, trigger: Optional[Trigger] = None):
        title = f"{'Редактирование' if trigger else 'Добавление'} триггера {trigger_name}"
        super().__init__(title=title)

        self.bot: TriggeredBot = bot
        self.trigger_name = trigger_name

        if trigger:
            self.pattern.default, self.msg.default, self.emoji.default, self.mode.default = \
                trigger.dict_parameters.values()

    pattern = TextInput(
        label="Паттерн",
        style=TextStyle.short,
        placeholder="Например: \".*доброе.*утро.*\"",
    )

    msg = TextInput(
        label="Ответное сообщение",
        style=TextStyle.long,
        placeholder="Например: \"Доброе утро!\"",
        required=False
    )

    emoji = TextInput(
        label="Эмодзи под сообщением",
        style=TextStyle.short,
        placeholder="Например: \"<:sunrise:>\"",
        required=False
    )

    mode = TextInput(
        label="Режим",
        style=TextStyle.short,
        placeholder="Например: \"3\" (сообщение и эмодзи)",
    )

    async def on_submit(self, interaction: Interaction) -> None:
        self.bot.db.set_trigger(
            guild=interaction.guild_id,
            trigger=Trigger(
                name=self.trigger_name,
                pattern=self.pattern.value,
                msg=self.msg.value,
                emoji=self.emoji.value,
                mode=self.mode.value
            )
        )
        self.bot.save_local_database()

        embed = Embed(
            title=self.title,
            description=f'**{self.pattern.label}** `{self.pattern}`\n'
                        f'**{self.msg.label}** {self.msg}\n'
                        f'**{self.emoji.label}** {self.emoji}\n'
                        f'**{self.mode.label}** `{self.mode}`\n',
            timestamp=datetime.now(),
            colour=Colour.default()
        )

        await interaction.response.send_message(embed=embed)
