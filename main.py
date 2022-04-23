import asyncio

from dotenv import load_dotenv
from clients.triggered_bot import TriggeredBot
from cogs.triggers import SlashTrigger
from cogs.settings import SlashSettings
from cogs.sync import CommandSync
import os
from database import GuildDatabase, BotDatabase
from discord import Intents


async def main():
    load_dotenv()
    DISCORD_TOKEN = os.environ['TOKEN']

    intents = Intents.default()
    intents.message_content = True

    my_bot = TriggeredBot(
        command_prefix='!',
        db=GuildDatabase.load_from_database(db=BotDatabase()),
        intents=intents,
    )

    await my_bot.add_cog(SlashTrigger(bot=my_bot))  # TODO guilds?
    await my_bot.add_cog(SlashSettings(bot=my_bot))
    await my_bot.add_cog(CommandSync())

    try:
        await my_bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        my_bot.db.save_all_guilds_to_db()
        await my_bot.close()


if __name__ == '__main__':
    asyncio.run(main())


# TODO help command
# TODO mention
