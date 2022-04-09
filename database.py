import dataclasses
from abc import ABC, abstractmethod

import redis
from redis.commands.json.path import Path
import os
from dotenv import load_dotenv

load_dotenv()


class NoGuildFoundError(Exception):
    pass


class BotDatabase(ABC):
    """Database for storing guilds and their triggers."""

    @property  # TODO delete
    @abstractmethod
    def get_db(self):
        """Returns DB instance."""
        ...

    @property
    @abstractmethod
    def _guilds(self) -> list[int]:
        """Returns list of ID's of all guilds having triggers set."""
        ...

    @abstractmethod
    def _get_guild(self, guild_id: int) -> dict:
        """Returns data of particular guild from Redis."""
        ...

    @abstractmethod
    def _save_guild(self, guild_data: dict) -> None:
        """Saves data of particular guild to Redis."""
        ...

    @abstractmethod
    def _add_guild(self, guild_id: int, guild_name: str = 'unknown') -> None:
        """Add an empty guild with given guild_id and empty dict of triggers."""
        ...

    @abstractmethod
    def get_triggers(self, _id: int) -> dict | None:
        """Returns dict of triggers of given guild or None if triggers are not defined."""
        ...

    @abstractmethod
    def get_trigger(self, guild_id: int, trigger: str) -> dict | None:
        """Returns asked trigger of given guild or None if trigger is not defined."""
        ...

    @abstractmethod
    def set_trigger(self, guild_id: int, name_of_trigger: str, trigger_data: dict) -> None:
        """Creates a guild if it does not exist and saves trigger to this guild."""
        ...

    @abstractmethod
    def _erase(self):
        """Delete all data from DB."""
        ...


class RedisDatabase(BotDatabase):
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
            raise NoGuildFoundError  # TODO custom errors
        return self._db.json().get(guild_id)

    def _save_guild(self, guild_data: dict) -> None:
        """Saves data of particular guild to Redis."""
        self._db.json().set(guild_data['id'], Path.root_path(), guild_data)

    def _add_guild(self, guild_id: int, guild_name: str = 'unknown') -> None:
        """Add an empty guild with given guild_id and empty dict of triggers."""
        # print(f'All guilds are: {self.guilds}')  # TODO logging
        if guild_id not in self._guilds:
            # print(f'Adding new guild: {name}@{guild_id}')  # TODO logging

            self._db.json().set(guild_id, Path.root_path(), {
                'id': guild_id,
                'name': guild_name,
                'triggers': {},  # TODO Empty dict?
                'settings': {},  # TODO Empty dict?
            })
            # print(f'Done!')  # TODO logging

    def get_triggers(self, _id: int) -> dict | None:
        """Returns dict of triggers of given guild or None if triggers are not defined."""
        return self._get_guild(guild_id=_id).get('triggers', None)

    def get_trigger(self, guild_id: int, trigger: str) -> dict | None:
        """Returns asked trigger of given guild or None if trigger is not defined."""
        return self._get_guild(guild_id=guild_id).get('triggers', {}).get(trigger, None)

    def set_trigger(self, guild_id: int, name_of_trigger: str, trigger_data: dict) -> None:
        """Creates a guild if it does not exist and saves trigger to this guild."""
        # print(f'Data: {guild_id} {name} {patterns} {msg} {emoji} {mode}')  # TODO logging
        if guild_id not in self._guilds:
            self._add_guild(guild_id=guild_id)

        guild_data = self._get_guild(guild_id=guild_id)
        guild_data['triggers'].update({name_of_trigger: trigger_data})  # TODO ['triggers'] to .get('triggers')
        self._save_guild(guild_data=guild_data)

    def _erase(self):
        """Delete all data from DB."""
        if input(f'Print password to erase all database: ') == '987654321':
            for key in self._db.keys():
                self._db.delete(key)


if __name__ == '__main__':
    r = RedisDatabase()

    from clients.triggered_bot import Trigger
    a = Trigger(name='ddd', pattern='sdf', msg='ggg')

    vbnw = {
        'id': 1231231,
        'name': 'VBNW',
        'triggers': {
            'triple_shot': {
                'patterns': [],
                'msg': 'triple.jpeg',
                'emoji': ':triple:',
                'mode': 0,
            },
            'stuhn': {
                'patterns': [],
                'msg': 'stuhn.jpeg',
                'emoji': ':stuhn:',
                'mode': 0,
            },
            a.name: a.serialize()
        },
        'settings': {
            # some stuff here
        }
    }

    assguard = {
        'id': 1245333,
        'name': 'AssGuard',
        'triggers': {
            'pariah': {
                'patterns': [],
                'msg': 'pariah.jpeg',
                'emoji': ':pariah:',
                'mode': 0,
            },
        },
        'settings': {
            # some stuff here
        }
    }

    r.get_db.json().set(vbnw['id'], Path.root_path(), vbnw)

    # r.redis.json().set(vbnw['id'], Path.root_path(), vbnw)
    # r.redis.json().set(assguard['id'], Path.root_path(), assguard)
    #
    aa = r.get_db.json().get(922919845450903573)
    print(aa)

    for trigger_name, trigger_data in aa['triggers'].items():
        a = Trigger.from_database(name=trigger_name, trigger=trigger_data)
        print(a)

# TODO backup
