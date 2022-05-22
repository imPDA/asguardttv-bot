from __future__ import annotations
import os
import time
from typing import Protocol, List, Optional, Dict, Any, TypeVar
from datetime import datetime, timedelta
import pickle

import redis
from redis.commands.json.path import Path

import abc
from errors import TriggerNotFoundError, GuildNotFoundError
from datatypes import Trigger, Settings, Guild, Build
from dotenv import load_dotenv

from pprint import pprint
from dataclasses import dataclass, field

load_dotenv()


class RedisDatabase(abc.ABC):
    def __init__(self,
                 host: Optional[str] = None,
                 port: Optional[int | str] = None,
                 password: Optional[str] = None,
                 ) -> None:
        self._db: redis.Redis = redis.StrictRedis(
            host=host if host else os.environ['REDIS_HOST'],
            port=port if port else int(os.environ['REDIS_PORT']),
            password=password if password else os.environ['REDIS_PASSWORD']
        )

    # TODO key 'int' - change to any basic type?
    T = TypeVar('T')

    def get(self, key: T) -> dict:
        """Returns value as :class:`dict` by given key from Redis."""
        return self._db.json().get(key)

    def set(self, key: T, value: dict) -> None:
        """Saves :class:`dict` value with given key to Redis."""
        self._db.json().set(key, Path.root_path(), value)

    def keys(self) -> list[T]:
        """Returns list of all keys from Redis."""
        return [key.decode() for key in self._db.keys()]


class MyRedisDatabase(RedisDatabase):
    """Redis DB for TriggeredBot."""

    def __init__(self,
                 host: Optional[str] = None,
                 port: Optional[int | str] = None,
                 password: Optional[str] = None) -> None:
        super().__init__(host=host, port=port, password=password)

    @property
    def builds_ids(self) -> List[int]:
        """List[:class:`int`] of builds' IDs."""

        return list(self.get(key=0)['builds'].keys())

    def get_build(self, id_: int) -> Build:
        """
        Returns :class:`Build` instance from Redis database.

        :param id_: ID of the guild.
        """

        if id_ not in self.builds_ids:
            raise GuildNotFoundError  # TODO custom errors

        build = (id_, self.get(key=0)['builds'].get(id_))
        return Build.from_database(build=build)

    def save_build(self, build: Build) -> None:
        """Saves particular :class:`Build` to Redis."""

        data = self.get(key=0)
        data['builds'].update({build.id: build.to_database})
        self.set(0, data)

    def save_builds(self, builds: Dict[int, Build]) -> None:
        """Saves all builds to Redis."""

        data = self.get(key=0)
        data['builds'] = builds
        self.set(0, data)

    @property
    def guilds_ids(self) -> List[int]:
        """List[:class:`int`] of guilds' IDs."""

        return [key for key in self.keys() if key != '0']

    def get_guild(self, id_: int) -> Guild:
        """
        Returns :class:`Guild` instance from Redis database.

        :param id_: ID of the guild.
        """

        if id_ not in self.guilds_ids:
            raise GuildNotFoundError  # TODO custom errors

        return Guild.from_database(guild_id=id_, data=self.get(id_))

    def save_guild(self, guild: Guild) -> None:
        """Saves particular :class:`Guild` to Redis."""

        self.set(guild.id, guild.to_database)

    # def get_triggers(self, guild: Guild) -> List[Trigger] | None:
    #     """
    #     Returns dict of triggers of given guild or None if triggers are not defined.
    #
    #     :param guild:
    #     :return:
    #     """
    #
    #     try:
    #         return guild.triggers
    #     except TypeError:  # ???
    #         return
    #     except AttributeError:  # ???
    #         # AttributeError: 'NoneType' object has no attribute 'get'
    #         return
    #
    # def get_trigger(self, guild: Guild, name: str) -> Trigger:
    #     """
    #     Returns asked trigger of given guild or raises an exception.
    #
    #     :param guild:
    #     :param name:
    #     :return:
    #     """
    #
    #     try:
    #         return Trigger.from_database(
    #             (name, self._get_guild(guild=guild).get('triggers').get(name))
    #         )
    #     except TypeError:
    #         print(f'{name} trigger not found.')  # TODO logging
    #         raise TriggerNotFoundError

    # def set_trigger(self, guild: DiscordGuild, trigger: Trigger) -> None:
    #     """
    #     Creates a guild if it does not exist and saves trigger to this guild.
    #
    #     :param guild:
    #     :param trigger:
    #     :return:
    #     """
    #
    #     # print(f'Data: {guild_id} {name} {patterns} {msg} {emoji} {mode}')  # TODO logging
    #     guild_data = self._get_guild(guild=guild)
    #     guild_data['triggers'].update(trigger.to_dict)
    #     self.save_guild(guild_id=guild, guild_data=guild_data)
    #
    # def get_settings(self, guild: DiscordGuild) -> Settings:
    #     return Settings.from_database(self._get_guild(guild=guild).get('settings'))
    #
    # def set_settings(self, guild: DiscordGuild, settings: Settings) -> None:
    #     data = self._get_guild(guild=guild)
    #     data['settings'].update(settings.to_dict)
    #     self.save_guild(guild_id=guild, guild_data=data)


@dataclass
class LocalDatabase:
    """
    Description.  # TODO
    """
    _guilds: Dict[int, Guild] = field(default_factory=dict)
    _builds: Dict[int, Build] = field(default_factory=dict)

    @property
    def builds(self):
        return self._builds

    # @staticmethod
    # def check_hash(func):
    #     def wrapper(*args, **kwargs):
    #         self = args[0]
    #         guild: Guild = kwargs.get('guild_id')
    #
    #         if isinstance(guild, int):
    #             guild = self._guilds[guild]
    #
    #         if guild and guild.last_check + timedelta(minutes=5) < datetime.now():
    #             print(guild.id)
    #             hash_from_db = self._db.get_guild(guild_id=guild.id).get('hash')
    #             if hash_from_db != guild.hash:
    #                 print('Different hashes!')  # TODO logging
    #                 self._db.save_guild(guild_id=guild)
    #             else:
    #                 print('Everything is up to date!')  # TODO logging
    #         return func(*args, **kwargs)
    #
    #     return wrapper

    # @check_hash
    @property
    def guilds(self):
        return self._guilds

    @classmethod
    def load_from_database(cls, db: MyRedisDatabase) -> LocalDatabase:
        return cls(
            _guilds={int(guild_id): db.get_guild(id_=guild_id) for guild_id in db.guilds_ids},
            _builds={int(build_id): db.get_build(id_=build_id) for build_id in db.builds_ids},
        )

    # def save_to_file(self):
    #     with open('data.pickle', 'wb') as f:
    #         pickle.dump(self._guilds, f)
    #
    # @classmethod
    # def read_from_file(cls):
    #     with open('data.pickle', 'rb') as f:
    #         return pickle.load(f)

    def set_guild(self, guild: Guild):
        if guild.id in self._guilds.keys():  # guild already exists
            return

        self._guilds[guild.id] = guild

    def save_to_redis_db(self, db: MyRedisDatabase):
        for guild in self._guilds.values():
            db.save_guild(guild)
        db.save_builds(self._builds)

    def set_trigger(self, guild: Guild | int, trigger: Trigger) -> None:
        """
        Saves the given :class:`Trigger` to :class:`LocalDatabase`.

        :param guild: Guild instance or ID.
        :param trigger: Trigger to save.
        """

        if isinstance(guild, int):
            guild = self._guilds[guild]

        self._guilds[int(guild.id)].triggers.update({trigger.name: trigger})


if __name__ == '__main__':
    redis = MyRedisDatabase()
    guild_db = LocalDatabase.load_from_database(db=redis)

    # local_db = GuildLocalDatabase()
    # local_db =

    pprint(guild_db)


# TODO backup with Task
