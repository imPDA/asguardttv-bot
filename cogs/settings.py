import asyncio

from discord.ext import commands
from clients.triggered_bot import TriggeredBot
from discord_argparse import ArgumentConverter, RequiredArgument, OptionalArgument


class Settings(commands.Cog):
    def __init__(self, bot: TriggeredBot):
        self.bot = bot

    trigger_arguments = ArgumentConverter(
        pattern=OptionalArgument(str, default=None),
        msg=OptionalArgument(str, default=None),
        emoji=OptionalArgument(str, default=None),
        mode=OptionalArgument(int, default=None)
    )

    @commands.command(name='trigger')
    @commands.has_permissions(administrator=True)
    async def trigger(self, ctx, name: str, *, trigger: trigger_arguments = trigger_arguments.defaults()):
        guild = ctx.guild.id

        if guild not in self.bot.db.guilds:
            self.bot.db.add_guild(guild)

        self.bot.db.add_trigger(guild_id=guild, name_of_trigger=name, trigger=trigger)  # TODO rename

        while True:
            count = 0
            t = self.bot.db.get_trigger(guild_id=guild, trigger=name)
            if t is not None:
                await ctx.channel.send(f'Trigger changed! Name={name}, pattern={t.get("pattern", "")}, '
                                       f'msg={t.get("msg", "")}, emoji={t.get("emoji", "")}, mode={t.get("mode", "")}')
                break
            else:
                count += 1
                await asyncio.sleep(1)
            if count >= 5:
                await ctx.channel.send(f'Something went wrong... Trigger {name} was not added...')
                break

    @trigger.error
    async def add_trigger_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            # print('You are not admin to change triggers')
            await ctx.channel.send('You are not admin to change triggers')
        else:
            print(error)

