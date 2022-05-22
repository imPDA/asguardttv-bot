import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed, Colour, TextStyle, SelectOption
from discord.ui import Modal, TextInput, Select, View, Button
from discord.app_commands.errors import MissingPermissions
from datetime import datetime
from typing import List, Optional

from clients.triggered_bot import TriggeredBot
from datatypes import Trigger, Build

from constants import ESO_CLASSES
from constants import ESO_LOCATIONS


class CustomButton(Button):
    def __init__(self, bot: TriggeredBot, *args, **kwargs):
        self.bot = bot
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: Interaction):
        build_type = None
        build_class = None
        build_locations = None
        build_availability = None

        for children in self.view.children:
            if isinstance(children, Select):
                if not children.values and not children.disabled:
                    await interaction.response.send_message(f"Нужно заполнить все поля!", ephemeral=True)
                    break
                match children.custom_id:
                    case 'class':
                        build_class = children.values[0]
                    case 'type':
                        build_type = children.values[0]
                    case 'availability':
                        if children.disabled:
                            build_availability = 'opened'
                        else:
                            build_availability = children.values[0]
                    case 'location':
                        build_locations = children.values
        else:
            await interaction.response.send_modal(
                ModalAddBuild(
                    bot=self.bot,
                    build_class=build_class,
                    build_type=build_type,
                    build_availability=build_availability,
                    build_locations=build_locations
                )
            )


class CustomSelect(Select):
    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class SlashBuilds(commands.Cog):
    """Description."""  # TODO
    def __init__(self, bot: TriggeredBot):
        self.bot: TriggeredBot = bot

    builds = app_commands.Group(
        name="builds",
        description="...",
    )

    @staticmethod
    def is_trusted_person():
        def predicate(interaction: Interaction) -> bool:
            return interaction.user.id in [
                408926967455285248,  # impda#9680 TODO addind on fly with command
                332997447678820373,  # VBNW#4625
                973696948651565086,  # neYa#8047

            ]

        return app_commands.check(predicate)

    @builds.command(name='add', description="Добавить новый билд")
    @is_trusted_person()
    async def add(self, interaction: Interaction):
        """Slash command to add a build."""

        button_continue = CustomButton(
            bot=self.bot,
            label="Дальше",
            disabled=False,
        )
        select_type = CustomSelect(
            placeholder="Спек (мана/стамина/...)",
            custom_id='type',
            options=[
                SelectOption(label="stam", emoji=None, description=None),
                SelectOption(label="mana", emoji=None, description=None),
                SelectOption(label="other", emoji=None, description=None),
            ]
        )
        select_class = CustomSelect(
            placeholder="Класс",
            custom_id='class',
            options=[SelectOption(
                label=class_name,
                emoji=details['emoji'] if details['emoji'] else None,
                description=details['description']if details['description'] else None)

                for class_name, details in ESO_CLASSES.items()]
        )
        select_location = CustomSelect(
            placeholder="Локация (множественный выбор)",
            custom_id='location',
            options=[SelectOption(
                label=location,
                emoji=details['emoji'] if details['emoji'] else None,
                description=details['description'] if details['description'] else None)

                for location, details in ESO_LOCATIONS.items()],
            min_values=1,
            max_values=6,
        )
        select_availability = CustomSelect(
            placeholder="Видимость",
            custom_id='availability',
            options=[
                SelectOption(label="opened", emoji=None,
                             description="Можно использовать на других серверах и DM", default=True),
                SelectOption(label="guild only", emoji=None,
                             description="Можно использовать только на этом сервере"),
            ],
            disabled=True if interaction.channel.type == discord.ChannelType.private else False
        )

        view = View()
        view.add_item(select_type)
        view.add_item(select_class)
        view.add_item(select_location)
        view.add_item(select_availability)

        view.add_item(button_continue)

        await interaction.response.send_message(view=view, ephemeral=True)

    @builds.command(name='find', description="Найти билд")
    async def find(self, interaction: Interaction, name: str):
        """Slash command to find a build."""

        build = {build.name: build for build in self.bot.db.builds.values()}[name]
        embed = Embed(
            title=f"{build.name}",
            description=
                f"**Спек** {build.type}\n"
                f"**Класс** {build.eso_class}\n"
                f"**Локации** {build.locations}\n"
                f"**Описание** {build.description}\n"
                f"**Автор** {build.author if build.author else 'Неизвестен'}\n"
                f"**Дата добавления** {build.added_time}\n",
            timestamp=datetime.now(),
            colour=Colour.default()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.followup.send(content=build.description, ephemeral=False)

    @find.autocomplete('name')
    async def find_name_autocomplete(
            self,
            interaction: Interaction,
            current: str
    ) -> List[app_commands.Choice[str]]:
        return [app_commands.Choice(name=build.name, value=build.name) for build
                in self.bot.db.builds.values() if
                build.guild == interaction.guild_id or build.availability == 'opened']

    @builds.command(name='list', description="Список всех билдов")
    @is_trusted_person()
    async def list(
            self,
            interaction: Interaction,
            guild_specific: bool = False,
            author: Optional[str] = None,
            my: bool = False) -> None:
        """Slash command to print out list of builds."""

        if my:
            my_builds = [build for build in self.bot.db.builds.values() if str(interaction.user.id) in build.added_by]
            embed_my_builds = Embed(
                title=f"Список добавленных {interaction.user.name} билдов",
                description="\n".join(
                    f"**{i + 1}. {build.name}**\n"
                    f"**Спек** {build.type}\n"
                    f"**Класс** {build.eso_class}\n"
                    f"**Локации** {build.locations}\n"
                    f"**Описание** {build.description}\n"
                    f"**Автор** {build.author if build.author else 'Неизвестен'}\n"
                    f"**Дата добавления** {build.added_time}\n"
                    for i, build in
                    enumerate(my_builds)
                ),
                timestamp=datetime.now(),
                colour=Colour.default()
            )
            if len(my_builds) == 0:
                await interaction.response.send_message(content="Не найдено билдов!", ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed_my_builds, ephemeral=True)
        else:
            guild_specific_builds = [build for build in self.bot.db.builds.values() if
                                     interaction.guild_id == build.guild and
                                     not build.availability == 'opened']
            other_builds = [] if guild_specific else \
                [build for build in self.bot.db.builds.values() if build.availability == 'opened' and
                 build not in guild_specific_builds]

            if author:
                guild_specific_builds = [build for build in guild_specific_builds if build.author == author]
                other_builds = [build for build in other_builds if build.author == author]

            if len(guild_specific_builds) == 0 and len(other_builds) == 0:
                await interaction.response.send_message(content="Не найдено билдов!", ephemeral=True)
            else:
                await interaction.response.defer()

            embed_guild_specific_builds = Embed(
                title=f"Список билдов в гильдии",
                description="\n".join(
                    f"**{i + 1}. {build.name}**\n"
                    f"**Спек** {build.type}\n"
                    f"**Класс** {build.eso_class}\n"
                    f"**Локации** {build.locations}\n"
                    f"**Описание** {build.description}\n"
                    f"**Автор** {build.author if build.author else 'Неизвестен'}\n"
                    f"**Дата добавления** {build.added_time}\n"
                    for i, build in
                    enumerate(guild_specific_builds)
                ),
                timestamp=datetime.now(),
                colour=Colour.default()
            )

            embed_other_builds = Embed(
                title=f"Прочие билды",
                description="\n".join(
                    f"**{i + 1}. {build.name}**\n"
                    f"**Спек** {build.type}\n"
                    f"**Класс** {build.eso_class}\n"
                    f"**Локации** {build.locations}\n"
                    f"**Описание** {build.description}\n"
                    f"**Автор** {build.author if build.author else 'Неизвестен'}\n"
                    f"**Дата добавления** {build.added_time}\n"
                    for i, build in
                    enumerate(other_builds)
                ),
                timestamp=datetime.now(),
                colour=Colour.default()
            )

            if len(guild_specific_builds) > 0:
                await interaction.followup.send(embed=embed_guild_specific_builds)
            if len(other_builds) > 0:
                await interaction.followup.send(embed=embed_other_builds)

    @list.autocomplete('author')
    async def list_author_autocomplete(
            self,
            interaction: Interaction,
            current: str
    ) -> List[app_commands.Choice[str]]:
        return [app_commands.Choice(name=build.author, value=build.author) for build
                in self.bot.db.builds.values() if
                (build.guild == interaction.guild_id or build.availability == 'opened') and
                (current in build.author or current == '')]

    @builds.command(name='delete', description="Удалить билд")
    @is_trusted_person()
    async def delete(self, interaction: Interaction, name: str):
        """Slash command to find a build."""

        delete_button = Button(label="Удалить", style=discord.ButtonStyle.danger)
        abort_button = Button(label="Отменить", style=discord.ButtonStyle.primary)

        async def delete_callback(interaction: Interaction) -> None:
            try:
                for id_, build in self.bot.db.builds.items():
                    if build.name == name:
                        if str(interaction.user.id) not in build.added_by:  # it was not you added build - can`t delete
                            await interaction.response.edit_message(
                                content=f"Ошибка удаления (билд был добавлен другим пользователем!).",
                                view=None,
                                embed=None
                            )
                        else:
                            self.bot.db.builds.pop(id_)
                            self.bot.save_local_database()
                            await interaction.response.edit_message(
                                content=f"Билд {name} удалён!",
                                view=None,
                                embed=None
                            )
                        break
            except KeyError:
                await interaction.response.edit_message(content=f"Ошибка удаления (KeyError).", view=None, embed=None)

        async def abort_callback(interaction: Interaction) -> None:
            await interaction.response.edit_message(content="Отменено.", view=None, embed=None)

        delete_button.callback = delete_callback
        abort_button.callback = abort_callback

        build = {build.name: build for build in self.bot.db.builds.values()}[name]
        embed = Embed(
            title=f"{build.name}",
            description=
                f"**Спек** {build.type}\n"
                f"**Класс** {build.eso_class}\n"
                f"**Локации** {build.locations}\n"
                f"**Описание** {build.description}\n"
                f"**Автор** {build.author if build.author else 'Неизвестен'}\n"
                f"**Дата добавления** {build.added_time}\n",
            timestamp=datetime.now(),
            colour=Colour.default()
        )

        view = View()
        view.add_item(delete_button)
        view.add_item(abort_button)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @delete.autocomplete('name')
    async def delete_name_autocomplete(
            self,
            interaction: Interaction,
            current: str
    ) -> List[app_commands.Choice[str]]:
        return [app_commands.Choice(name=build.name, value=build.name) for build
                in self.bot.db.builds.values() if
                str(interaction.user.id) in build.added_by]  # if you added the build you can delete it

    @add.error
    async def add_error(self, interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("Недостаточно прав для использования команды", ephemeral=True)

    @list.error
    async def list_error(self, interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("Недостаточно прав для использования команды", ephemeral=True)
        else:
            print(error)

    @delete.error
    async def delete_error(self, interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("Недостаточно прав для использования команды", ephemeral=True)


class ModalAddBuild(Modal):
    """
    Yes, it is Description. TODO
    """

    def __init__(self,
                 bot: TriggeredBot,
                 build_class: str,
                 build_type: str,
                 build_availability: str,
                 build_locations: List[str]) -> None:
        title = f"{build_type} {build_class} билд"
        super().__init__(title=title)

        self.build_class = build_class
        self.build_type = build_type
        self.build_availability = build_availability
        self.build_locations = build_locations

        self.bot: TriggeredBot = bot

    name = TextInput(
        label="Название",
        style=TextStyle.short,
        placeholder="Например: \"streakDO\"",
        required=True
    )

    description = TextInput(
        label="Описание билда",
        style=TextStyle.long,
        placeholder="Можно добавить ссылку на картинку с SuperStar/ESO Build Editor/YouTube/... или текстовое описание",
        required=True
    )

    author = TextInput(
        label="Автор (не обязательно)",
        style=TextStyle.short,
        placeholder="ID в игре или на твиче/Discord/...",
        required=False
    )

    async def on_submit(self, interaction: Interaction) -> None:
        if self.bot.db.builds:
            new_id = max(self.bot.db.builds) + 1
        else:
            new_id = 100_000

        self.bot.db.builds.update({
            new_id: Build(
                id=new_id,
                name=self.name.value,
                eso_class=self.build_class,
                type=self.build_type,
                availability=self.build_availability,
                locations=self.build_locations,
                description=self.description.value,
                author=self.author.value,
                added_by=f"@{interaction.user.name}#{interaction.user.discriminator}<{interaction.user.id}>",
                added_time=datetime.now().strftime("%d.%m.%Y %H:%M"),
                guild=interaction.guild_id,
                # emoji: Optional[str] = None,
            )
        })
        self.bot.save_local_database()

        embed = Embed(
            title=self.name,
            description=f"**{self.title}**\n"
                        f"**для** {' '.join(self.build_locations)}\n"
                        f"**{self.description.label}** {self.description}\n",
            timestamp=datetime.now(),
            colour=Colour.default()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
