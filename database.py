import os
from typing import Protocol

import redis
from redis.commands.json.path import Path

from datatypes import Trigger
from dotenv import load_dotenv

load_dotenv()


class GuildNotFoundError(Exception):
    pass


class TriggerNotFoundError(Exception):
    pass


class BotDatabase(Protocol):
    """Database for storing guilds and their triggers."""

    def _guilds(self) -> list[int]:
        """Returns list of all guilds (ID's) having triggers set."""

    def _get_guild(self, guild_id: int) -> dict:
        """Returns data of particular guild from database by ID."""

    def _save_guild(self, guild_id: int, guild_data: dict) -> None:
        """Saves data of particular guild to database."""

    def _erase(self):
        """Delete all data from DB."""


class RedisTriggeredBotDatabase(BotDatabase):
    """Redis DB located on AWS"""

    def __init__(self,
                 host: str = os.environ['REDIS_HOST'],
                 port: int = int(os.environ['REDIS_PORT']),
                 password: str = os.environ['REDIS_PASSWORD']
                 ):
        # super(BotDatabase, self).__init__()
        self._db: redis.Redis = redis.StrictRedis(host=host, port=port, password=password)

    @property  # TODO delete
    def get_db(self) -> redis.Redis:
        """Returns DB instance."""
        return self._db

    @property
    def _guilds(self) -> list[int]:
        """Returns list of ID's of all guilds having triggers set."""
        return [int(key.decode()) for key in self._db.keys()]

    def _get_guild(self, guild_id: int) -> dict:
        """Returns data of particular guild from Redis."""
        if guild_id not in self._guilds:
            raise GuildNotFoundError  # TODO custom errors
        return self._db.json().get(guild_id)

    def _save_guild(self, guild_id: int, guild_data: dict) -> None:
        """Saves data of particular guild to Redis."""
        self._db.json().set(guild_id, Path.root_path(), guild_data)

    def get_triggers(self, guild_id: int) -> list[Trigger] | None:
        """Returns dict of triggers of given guild or None if triggers are not defined."""
        try:
            return [Trigger.from_database(item) for item in self._get_guild(guild_id=guild_id).get('triggers').items()]
        except TypeError:
            return

    def get_trigger(self, guild_id: int, trigger_name: str) -> Trigger:
        """Returns asked trigger of given guild or raises an exception."""
        try:
            return Trigger.from_database(
                (trigger_name, self._get_guild(guild_id=guild_id).get('triggers').get(trigger_name))
            )
        except AttributeError:
            raise TriggerNotFoundError

    def set_trigger(self, guild_id: int, trigger: Trigger) -> None:
        """Creates a guild if it does not exist and saves trigger to this guild."""
        # print(f'Data: {guild_id} {name} {patterns} {msg} {emoji} {mode}')  # TODO logging
        try:
            guild_data = self._get_guild(guild_id=guild_id)
        except GuildNotFoundError:
            guild_data = {
                'name': 'unknown',
                'triggers': {},
            }
        guild_data['triggers'].update({trigger.name: trigger.dict_parameters})
        self._save_guild(guild_id=guild_id, guild_data=guild_data)


if __name__ == '__main__':
    r = RedisTriggeredBotDatabase()

# TODO backup
