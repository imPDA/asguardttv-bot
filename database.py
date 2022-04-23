from __future__ import annotations
import os
import time
from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime, timedelta
from pprint import pprint
import pickle

import redis
from redis.commands.json.path import Path

import abc
from errors import TriggerNotFoundError, GuildNotFoundError
from datatypes import Trigger, Settings, DiscordGuild, DiscordObject, Guild
from dotenv import load_dotenv

from pprint import pprint
from dataclasses import dataclass, field

load_dotenv()


class BotDatabase(abc.ABC):
    """Base database."""  # TODO rewrite

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

    # def guilds(self) -> List[DiscordObject]:
    #     """Returns list of all guilds having triggers set."""

    def _get_guild(self, guild: DiscordGuild) -> dict:
        """Returns data of particular guild from database by ID."""

    # def save_guild(self, guild: DiscordGuild, guild_data: dict) -> None:
    #     """Saves data of particular guild to database."""

    def _erase(self):
        """Delete all data from DB."""

    """New part."""
    def get_guild(self, guild_id: int) -> Dict:
        return self._db.json().get(guild_id)

    def save_guild(self, guild: Guild) -> None:
        self._db.json().set(guild.id, Path.root_path(), guild.to_db)

    def keys(self) -> List[int]:
        return [int(key.decode()) for key in self._db.keys()]


class RedisTriggeredBotDatabase(BotDatabase):
    """Redis DB for TriggeredBot."""

    def __init__(self,
                 host: Optional[str] = None,
                 port: Optional[int | str] = None,
                 password: Optional[str] = None,
                 ) -> None:
        super().__init__(host=host, port=port, password=password)

    @property  # TODO delete
    def get_db(self) -> redis.Redis:
        """Returns DB instance."""
        return self._db

    @property
    def guilds(self) -> List[DiscordObject]:
        """Returns list of ID's of all guilds having triggers set."""
        return [DiscordObject(id=(key.decode())) for key in self._db.keys()]

    def _get_guild(self, guild: DiscordGuild) -> dict:
        """Returns data of particular guild from Redis."""
        if guild.id not in [_guild.id for _guild in self.guilds]:
            raise GuildNotFoundError  # TODO custom errors
        return self._db.json().get(guild.id)

    def save_guild(self, guild: DiscordGuild, guild_data: dict) -> None:
        """Saves data of particular guild to Redis."""
        self._db.json().set(guild.id, Path.root_path(), guild_data)

    def create_empty_guild(self, guild: DiscordGuild) -> None:
        self.save_guild(guild=guild, guild_data={
            'name': guild.name,
            'triggers': {},
            'settings': Settings().to_dict,
        })

    def get_triggers(self, guild: DiscordGuild) -> List[Trigger] | None:
        """Returns dict of triggers of given guild or None if triggers are not defined."""
        try:
            return [Trigger.from_database(item) for item in self._get_guild(guild=guild).get('triggers').items()]
        except TypeError:
            return
        except AttributeError:
            # AttributeError: 'NoneType' object has no attribute 'get'
            return

    def get_trigger(self, guild: DiscordGuild, name: str) -> Trigger:
        """Returns asked trigger of given guild or raises an exception."""
        try:
            return Trigger.from_database(
                (name, self._get_guild(guild=guild).get('triggers').get(name))
            )
        except TypeError:
            print(f'{name} trigger not found.')  # TODO logging
            raise TriggerNotFoundError

    def set_trigger(self, guild: DiscordGuild, trigger: Trigger) -> None:
        """Creates a guild if it does not exist and saves trigger to this guild."""
        # print(f'Data: {guild_id} {name} {patterns} {msg} {emoji} {mode}')  # TODO logging
        guild_data = self._get_guild(guild=guild)
        guild_data['triggers'].update(trigger.to_dict)
        self.save_guild(guild=guild, guild_data=guild_data)

    def get_settings(self, guild: DiscordGuild) -> Settings:
        return Settings.from_database(self._get_guild(guild=guild).get('settings'))

    def set_settings(self, guild: DiscordGuild, settings: Settings) -> None:
        data = self._get_guild(guild=guild)
        data['settings'].update(settings.to_dict)
        self.save_guild(guild=guild, guild_data=data)


@dataclass
class GuildDatabase:
    """Description"""  # TODO
    _db: BotDatabase
    _guilds: Dict[int, Guild] = field(default_factory=dict)

    @staticmethod
    def check_hash(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            guild: Guild = kwargs.get('guild_id')

            if isinstance(guild, int):
                guild = self._guilds[guild]

            if guild and guild.last_check + timedelta(minutes=5) < datetime.now():
                hash_from_db = self._db.get_guild(guild_id=guild.id).get('hash')
                if hash_from_db != guild.hash:
                    print('Different hashes!')  # TODO logging
                    self._db.save_guild(guild=guild)
                else:
                    print('Everything is up to date!')  # TODO logging
            return func(*args, **kwargs)
        return wrapper

    @check_hash
    def guild(self, guild_id: int) -> Guild:
        return self._guilds[guild_id]

    @property
    def guilds(self):
        return self._guilds

    @classmethod
    def load_from_database(cls, db: BotDatabase) -> GuildDatabase:
        return cls(
            _db=db,
            _guilds={key: Guild.from_db(guild_id=key, data=db.get_guild(guild_id=key)) for key in db.keys()}
        )

    def save_to_file(self):
        with open('data.pickle', 'wb') as f:
            pickle.dump(self._guilds, f)

    @classmethod
    def read_guilds_from_file(cls):
        with open('data.pickle', 'rb') as f:
            return pickle.load(f)

    def add_new_guild(self, guild: DiscordGuild):
        if guild.id in self._guilds.keys():  # TODO guild already exists
            return
        self._guilds[guild.id] = Guild(
                id=guild.id,
                name=guild.name,
        )

    def save_all_guilds_to_db(self):
        for guild in self._guilds.values():
            self._db.save_guild(guild=guild)


if __name__ == '__main__':
    r = BotDatabase()

    nya = Trigger(
        name="ня",
        pattern=".*ня.*",
        emoji="<:nya:45336425623423>",
        mode="2"
    )

    woof = Trigger(
        name="гав",
        pattern=".*гав.*",
        emoji="<:woof:0344633434563>",
        mode="2"
    )

    my_best_guild = Guild(
        id=922919845450903573,
        name="MyBestGuildEver",
        triggers=[
            Trigger.from_database((nya.name, nya)),
            Trigger.from_database((woof.name, woof))
        ]
    )

    my_best_guilds = GuildDatabase(
        _guilds=[my_best_guild],
        _db=r,
    )

# TODO backup
