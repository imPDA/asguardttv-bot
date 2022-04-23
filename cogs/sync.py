from discord.ext import commands
from discord import Object, HTTPException, Forbidden
from typing import Optional, Literal


class CommandSync(commands.Cog):
    """Description."""  # TODO

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context) -> None:
        fmt = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(fmt)} commands globally"
        )

    @sync.error
    async def sync_error(self, ctx, error):
        print(error)
