import asyncio
import os
from dotenv import load_dotenv

from discord import Intents
from clients.triggered_bot import TriggeredBot
from cogs.sync import CommandSync

from database import LocalDatabase, MyRedisDatabase

from cogs.slash_triggers import SlashTriggers
from cogs.slash_settings import SlashSettings
from cogs.slash_builds import SlashBuilds
from cogs.slash_sets import SlashSets


async def main():
    load_dotenv()
    DISCORD_TOKEN = os.environ['TOKEN']

    intents = Intents.default()
    intents.message_content = True

    remote_database = MyRedisDatabase()

    my_bot = TriggeredBot(
        command_prefix='!',
        remote_database=remote_database,
        intents=intents,
    )

    await my_bot.add_cog(SlashTriggers(bot=my_bot))
    # await my_bot.add_cog(SlashSettings(bot=my_bot))
    await my_bot.add_cog(CommandSync())
    await my_bot.add_cog(SlashBuilds(bot=my_bot))
    await my_bot.add_cog(SlashSets())

    try:
        await my_bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        my_bot.db.save_to_redis_db(db=remote_database,)
        await my_bot.close()


if __name__ == '__main__':
    asyncio.run(main())


# TODO help command
