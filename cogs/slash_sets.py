import random
import string
import redis
import io

import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed, Colour, TextStyle, SelectOption
from discord.ui import Modal, TextInput, Select, View, Button
from discord.app_commands.errors import MissingPermissions
from datetime import datetime
from typing import List, Optional, Tuple

from clients.triggered_bot import TriggeredBot
from PIL import Image


class SlashSets(commands.Cog):
    """Description."""  # TODO
    def __init__(self):
        self.eso_sets_db = redis.StrictRedis(  # TODO DELETE B4 PRODUCTION
            host='discord-bot-201.redis.a.osc-fr1.scalingo-dbs.com',
            port=38739,
            password='q15kv-bBaWC48hN9qFY7',
            ssl=True,
            ssl_cert_reqs='required',
            ssl_ca_certs=r'C:\Users\dimax\PycharmProjects\imPDA\eso_gear_reader\helpers\ca.pem',
        )
        self.names_of_sets = [key.decode('utf-8')[4:] for key in self.eso_sets_db.keys("set_*")]

    sets = app_commands.Group(
        name="sets",
        description="...",
    )

    def create_eso_set_embed(self, name: str) -> Tuple[discord.File, Embed]:
        set_description = self.eso_sets_db.get(f"set_{name}")
        if not set_description:
            raise KeyError('No such set in RedisDatabase')

        embed = Embed(
            title=f"{name}",
            description=set_description.decode('utf-8'),
            timestamp=datetime.now(),
            colour=Colour.default()
        )

        icon_name = self.eso_sets_db.get(f"icon_{name}").decode('utf-8')
        thumbnail = self.eso_sets_db.get(icon_name)
        # with io.BytesIO() as image_binary:
        #     Image.open(io.BytesIO(thumbnail)).save(image_binary, 'PNG')
        #     image_binary.seek(0)
        #     file = discord.File(image_binary, filename="thumbnail.png")
        #     embed.set_thumbnail(url="attachment://thumbnail.png")
        with io.BytesIO(thumbnail) as image_binary:
            file = discord.File(image_binary, filename=f"{icon_name}.png")
            embed.set_thumbnail(url=f"attachment://{icon_name}.png")

        return file, embed

    @sets.command(name='find', description="Найти сет")
    async def find(self, interaction: Interaction, name: str):
        """Slash command to find a set."""

        try:
            file, embed = self.create_eso_set_embed(name)
        except KeyError:
            sets = [set_name for set_name in self.names_of_sets if name.lower() in set_name.lower()]
            if len(sets) == 1:
                file, embed = self.create_eso_set_embed(sets[0])
            else:
                file = None
                embed = Embed(
                    title=f"...{name}...",
                    description='\n'.join(sets)+"\n...",
                    timestamp=datetime.now(),
                    colour=Colour.default()
                )
                embed.set_thumbnail(url="https://us.v-cdn.net/5020507/uploads/bf47ba6b81f347a352defdda0e8d80d5.png")

        if file:
            await interaction.response.send_message(file=file, embed=embed)
        else:
            await interaction.response.send_message(embed=embed)

    @find.autocomplete('name')
    async def find_name_autocomplete(
            self,
            interaction: Interaction,
            current: str
    ) -> List[app_commands.Choice[str]]:
        return [app_commands.Choice(name=set_name, value=set_name) for set_name
                in self.names_of_sets if current.lower() in set_name.lower()][:24]

    # @sets.command(name='list', description="Список всех сетов")
    # async def list(
    #         self,
    #         interaction: Interaction,
    #         guild_specific: bool = False,
    #         author: Optional[str] = None,
    #         my: bool = False) -> None:
    #     """Slash command to print out list of builds."""
    #
    #     if my:
    #         my_builds = [build for build in self.bot.db.builds.values() if str(interaction.user.id) in build.added_by]
    #         embed_my_builds = Embed(
    #             title=f"Список добавленных {interaction.user.name} билдов",
    #             description="\n".join(
    #                 f"**{i + 1}. {build.name}**\n"
    #                 f"**Спек** {build.type}\n"
    #                 f"**Класс** {build.eso_class}\n"
    #                 f"**Локации** {build.locations}\n"
    #                 f"**Описание** {build.description}\n"
    #                 f"**Автор** {build.author if build.author else 'Неизвестен'}\n"
    #                 f"**Дата добавления** {build.added_time}\n"
    #                 for i, build in
    #                 enumerate(my_builds)
    #             ),
    #             timestamp=datetime.now(),
    #             colour=Colour.default()
    #         )
    #         if len(my_builds) == 0:
    #             await interaction.response.send_message(content="Не найдено билдов!", ephemeral=True)
    #         else:
    #             await interaction.response.send_message(embed=embed_my_builds, ephemeral=True)
    #     else:
    #         guild_specific_builds = [build for build in self.bot.db.builds.values() if
    #                                  interaction.guild_id == build.guild and
    #                                  not build.availability == 'opened']
    #         other_builds = [] if guild_specific else \
    #             [build for build in self.bot.db.builds.values() if build.availability == 'opened' and
    #              build not in guild_specific_builds]
    #
    #         if author:
    #             guild_specific_builds = [build for build in guild_specific_builds if build.author == author]
    #             other_builds = [build for build in other_builds if build.author == author]
    #
    #         if len(guild_specific_builds) == 0 and len(other_builds) == 0:
    #             await interaction.response.send_message(content="Не найдено билдов!", ephemeral=True)
    #         else:
    #             await interaction.response.defer()
    #
    #         embed_guild_specific_builds = Embed(
    #             title=f"Список билдов в гильдии",
    #             description="\n".join(
    #                 f"**{i + 1}. {build.name}**\n"
    #                 f"**Спек** {build.type}\n"
    #                 f"**Класс** {build.eso_class}\n"
    #                 f"**Локации** {build.locations}\n"
    #                 f"**Описание** {build.description}\n"
    #                 f"**Автор** {build.author if build.author else 'Неизвестен'}\n"
    #                 f"**Дата добавления** {build.added_time}\n"
    #                 for i, build in
    #                 enumerate(guild_specific_builds)
    #             ),
    #             timestamp=datetime.now(),
    #             colour=Colour.default()
    #         )
    #
    #         embed_other_builds = Embed(
    #             title=f"Прочие билды",
    #             description="\n".join(
    #                 f"**{i + 1}. {build.name}**\n"
    #                 f"**Спек** {build.type}\n"
    #                 f"**Класс** {build.eso_class}\n"
    #                 f"**Локации** {build.locations}\n"
    #                 f"**Описание** {build.description}\n"
    #                 f"**Автор** {build.author if build.author else 'Неизвестен'}\n"
    #                 f"**Дата добавления** {build.added_time}\n"
    #                 for i, build in
    #                 enumerate(other_builds)
    #             ),
    #             timestamp=datetime.now(),
    #             colour=Colour.default()
    #         )
    #
    #         if len(guild_specific_builds) > 0:
    #             await interaction.followup.send(embed=embed_guild_specific_builds)
    #         if len(other_builds) > 0:
    #             await interaction.followup.send(embed=embed_other_builds)

    @find.error
    async def add_error(self, interaction, error):
        print(error)

    # @list.error
    # async def list_error(self, interaction, error):
    #     if isinstance(error, MissingPermissions):
    #         await interaction.response.send_message("Недостаточно прав для использования команды", ephemeral=True)
    #     else:
    #         print(error)
