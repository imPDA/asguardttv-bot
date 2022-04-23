from __future__ import annotations

from enums import ResponseMode
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json

from discord import Guild as DiscordGuild, Object as DiscordObject


__all__ = [
    DiscordGuild,
    DiscordObject,
]


@dataclass
class Trigger:
    name: str
    pattern: str = None
    msg: str = None
    emoji: str = None
    mode: Any = ResponseMode.OFF

    def __post_init__(self):
        try:
            self.mode = ResponseMode(int(self.mode))
        except ValueError as e:
            raise e

    @classmethod
    def from_database(cls, trigger: tuple) -> Trigger | None:
        name, trigger_data = trigger
        return cls(
            name=name,
            pattern=trigger_data['pattern'],
            msg=trigger_data.get('msg'),
            emoji=trigger_data.get('emoji'),
            mode=trigger_data['mode']
        )

    @property
    def to_dict(self) -> dict:
        return {
            self.name: self.dict_parameters
        }

    @property
    def dict_parameters(self) -> dict:
        return {
            'pattern': self.pattern,
            'msg': self.msg,
            'emoji': self.emoji,
            'mode': self.mode.value
        }


@dataclass()
class Settings:
    restricted: bool = False
    allowed_channel: str = None

    @classmethod
    def from_database(cls, settings: dict) -> Settings | None:
        return cls(
            restricted=settings.get('restricted'),
            allowed_channel=settings.get('allowed_channel'),
        )

    @property
    def to_dict(self) -> dict:
        return {
            'restricted': self.restricted,
            'allowed_channel': self.allowed_channel,
        }


@dataclass
class Guild:
    id: int  # frozen
    name: Optional[str]
    triggers: Optional[Dict[str, Trigger]] = field(default_factory=dict)
    settings: Settings = Settings()
    last_check: datetime = datetime.now()  # TODO rewrite

    @property
    def to_json(self) -> dict:
        return {
            'name': self.name,
            'triggers': {_id: trigger.dict_parameters for _id, trigger in self.triggers.items()},  # TODO map?
            'settings': self.settings.to_dict
        }

    @property
    def to_db(self):
        d = self.to_json
        d['hash'] = self.hash
        return d

    @classmethod
    def from_db(cls, guild_id: int, data: dict) -> Guild:
        return cls(
            id=guild_id,
            name=data.get('name'),
            triggers={kv_trigger[0]: Trigger.from_database(kv_trigger) for kv_trigger in data.get('triggers').items()},
            settings=Settings.from_database(data.get('settings')),
            last_check=datetime.now(),
        )

    @property
    def hash(self) -> str:
        dhash = hashlib.md5()
        encoded = json.dumps(self.to_json, sort_keys=True).encode()
        dhash.update(encoded)
        return dhash.hexdigest()

    # def get_trigger(self, name: str) -> Trigger:
    #     for trigger in self.triggers:
    #         if trigger.name == name:
    #             return trigger

    # def set_trigger(self, name: str, data: Trigger) -> None:
    #
    #     for i, trigger in enumerate(self.triggers):
    #         if trigger.name == name:
    #             self.triggers[i] = data
    #             return
