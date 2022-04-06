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
    def redis(self) -> redis.Redis:
        return self._redis

    @property
    @abstractmethod
    def guilds(self) -> list[int]:
        raise NotImplemented

    @abstractmethod
    def _get_guild(self, _id: int) -> dict:
        raise NotImplemented

    @abstractmethod
    def _save_guild(self, guild_data: dict) -> None:
        raise NotImplemented

    @abstractmethod
    def add_guild(self, guild_id: int, name: str = 'unknown') -> None:
        raise NotImplemented

    @abstractmethod
    def get_triggers(self, _id: int) -> dict:
        raise NotImplemented

    @abstractmethod
    def get_trigger(self, guild_id: int, trigger: str) -> dict:
        raise NotImplemented

    @abstractmethod
    def add_trigger(self, guild_id: int, name_of_trigger: str, trigger: dict) -> None:
        raise NotImplemented

    @abstractmethod
    def erase(self):
        raise NotImplemented


class RedisDatabase(BotDatabase):
    """Redis DB located on AWS"""

    def __init__(self,
                 host: str = os.environ['REDIS_HOST'],
                 port: int = int(os.environ['REDIS_PORT']),
                 password: str = os.environ['REDIS_PASSWORD']
                 ):
        super(BotDatabase, self).__init__()
        self._redis: redis.Redis = redis.StrictRedis(host=host, port=port, password=password)

    @property  # TODO delete
    def redis(self) -> redis.Redis:
        return self._redis

    @property
    def guilds(self) -> list[int]:
        """Returns list of ID's of all guilds having triggers set."""
        return [int(key.decode()) for key in self._redis.keys()]

    def _get_guild(self, _id: int) -> dict:
        return self._redis.json().get(_id)

    def _save_guild(self, guild_data: dict) -> None:
        self._redis.json().set(guild_data['id'], Path.root_path(), guild_data)

    def add_guild(self, guild_id: int, name: str = 'unknown') -> None:
        # print(f'All guilds are: {self.guilds}')  # TODO logging
        if guild_id not in self.guilds:
            # print(f'Adding new guild: {name}@{guild_id}')  # TODO logging
            new_guild = {
                'id': guild_id,
                'name': name,
                'triggers': {},
                'settings': {},
            }

            self._redis.json().set(guild_id, Path.root_path(), new_guild)
            # print(f'Done!')  # TODO logging

    def get_triggers(self, _id: int) -> dict:
        if _id not in self.guilds:  # TODO to get guild
            return {}  # TODO Exception ?
        return self._get_guild(_id=_id).get('triggers', {})

    def get_trigger(self, guild_id: int, trigger: str) -> dict:
        if guild_id not in self.guilds:  # TODO to get guild
            return {}  # TODO Exception ?
        return self._get_guild(_id=guild_id).get('triggers', {}).get(trigger, {})

    def add_trigger(self, guild_id: int, name_of_trigger: str, trigger: dict) -> None:
        if guild_id not in self.guilds:
            raise NoGuildFoundError

        # print(f'Data: {guild_id} {name} {patterns} {msg} {emoji} {mode}')  # TODO logging
        guild_data = self._get_guild(_id=guild_id)
        guild_data['triggers'].update({name_of_trigger: trigger})
        self._save_guild(guild_data=guild_data)

    def erase(self):
        if input(f'Print password to erase all database: ') == '987654321':
            for key in self._redis.keys():
                self._redis.delete(key)


if __name__ == '__main__':
    r = RedisDatabase()

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
            }
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

    # r.redis.json().set(vbnw['id'], Path.root_path(), vbnw)
    # r.redis.json().set(assguard['id'], Path.root_path(), assguard)
    #
    # print(r.guilds)
