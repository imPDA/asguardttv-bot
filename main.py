from dotenv import load_dotenv
from clients.triggered_bot import TriggeredBot
from cogs.settings import Settings
import os
from database import RedisDatabase


def main():
    load_dotenv()

    DISCORD_TOKEN = os.environ['TOKEN']

    my_bot = TriggeredBot(
        command_prefix='!',
        db=RedisDatabase()
    )

    my_bot.add_cog(Settings(bot=my_bot))
    my_bot.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()

