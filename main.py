import asyncio

from dotenv import load_dotenv
from clients.triggered_bot import TriggeredBot
from cogs.settings_v2 import Settings
import os
from database import RedisDatabase
from discord import Intents


async def main():
    load_dotenv()

    DISCORD_TOKEN = os.environ['TOKEN']
    intents = Intents.default()
    intents.message_content = True

    my_bot = TriggeredBot(
        command_prefix='!',
        db=RedisDatabase(),
        intents=intents
    )

    await my_bot.add_cog(Settings(bot=my_bot))
    await my_bot.start(DISCORD_TOKEN)


if __name__ == '__main__':
    asyncio.run(main())

# TODO help command

