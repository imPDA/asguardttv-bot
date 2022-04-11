import asyncio

from dotenv import load_dotenv
from clients.triggered_bot import TriggeredBot
from cogs.settings import Settings
import os
from database import RedisTriggeredBotDatabase
from discord import Intents, Object


async def main():
    load_dotenv()

    DISCORD_TOKEN = os.environ['TOKEN']
    intents = Intents.default()
    intents.message_content = True

    my_bot = TriggeredBot(
        command_prefix='!',
        db=RedisTriggeredBotDatabase(),
        intents=intents
    )

    await my_bot.add_cog(
        Settings(bot=my_bot),
        guilds=[  # TODO-1 to .env  TODO-2 do i need it?
            Object(id='922919845450903573'),
            Object(id='699083894179495940'),
        ]
    )
    await my_bot.start(DISCORD_TOKEN)


if __name__ == '__main__':
    asyncio.run(main())

# TODO help command

