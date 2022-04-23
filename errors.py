from discord import app_commands


class WrongChannel(app_commands.CheckFailure):
    pass


class GuildNotFoundError(Exception):
    pass


class TriggerNotFoundError(Exception):
    pass
