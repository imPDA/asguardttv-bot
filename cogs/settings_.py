"""
DEPRECATED VERSION
"""

from discord.ext import commands
from discord_argparse import ArgumentConverter, OptionalArgument
from discord.components import ComponentType, Button, ButtonStyle
from discord.types.components import ButtonComponent

from clients.triggered_bot import TriggeredBot


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='buttontest')
    @commands.has_permissions(administrator=True)
    async def trigger_v3(self, ctx: commands.Context):
        view = Buttons()

        await ctx.channel.send(
            content="Message Here",
            view=view,
        )

    trigger_arguments = ArgumentConverter(
        pattern=OptionalArgument(str, default=None),
        msg=OptionalArgument(str, default=None),
        emoji=OptionalArgument(str, default=None),
        mode=OptionalArgument(int, default=None)
    )

    @commands.command(name='trigger')
    @commands.has_permissions(administrator=True)
    async def trigger(self, ctx: commands.Context, name: str, *,
                      trigger: trigger_arguments = trigger_arguments.defaults()):
        guild_id = ctx.guild.id
        if any(trigger.get(v) is None or '' for v in ['pattern', 'mode']) or \
                all(trigger.get(v) is None or '' for v in ['msg', 'emoji']):
            await ctx.channel.send('Wrong input!')
            await ctx.message.add_reaction('❎')
            return

        # TODO add function 1
        self.bot.db.set_trigger(guild_id=guild_id, name_of_trigger=name, trigger_data=trigger)

        if self.bot.db.get_trigger(guild_id=guild_id, trigger=name) is not None:
            await ctx.message.add_reaction('✅')
        else:
            await ctx.message.add_reaction('❎')
            await ctx.channel.send(f'Something went wrong... Trigger {name} was not added...')
        # TODO add function 1

    @commands.command(name='trigger_v2')
    @commands.has_permissions(administrator=True)
    async def trigger_v2(self, ctx: commands.Context, name: str):
        guild_id = ctx.guild.id

        self.bot.start_configuration(name, ctx)
        await ctx.channel.send('Введите паттерн:')

    @trigger.error
    async def add_trigger_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            # print('You are not admin to change triggers')
            await ctx.channel.send('You are not administrator')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(error)
        else:
            print(error)
