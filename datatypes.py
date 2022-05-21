from __future__ import annotations

from pprint import pprint

from enums import ResponseMode
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json


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
    name: Optional[str] = "Unknown"
    triggers: Optional[Dict[str, Trigger]] = field(default_factory=dict)
    settings: Settings = Settings()
    last_check: datetime = datetime.now()  # TODO rewrite

    @property
    def to_json(self) -> dict:
        if self.triggers:
            triggers = {trigger.name: trigger.dict_parameters for trigger in self.triggers.values()}
        else:
            triggers = {}

        return {
            'name': self.name,
            'triggers': triggers,
            'settings': self.settings.to_dict
        }

    @property
    def to_database(self):
        d = self.to_json
        d['hash'] = self.hash
        return d

    @classmethod
    def from_database(cls, guild_id: int, data: dict) -> Guild:
        return cls(
            id=int(guild_id),
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

    def __eq__(self, other):
        if isinstance(other, Guild):
            return self.id == other.id
        if isinstance(other, int):
            return self.id == other


@dataclass
class Build:
    id: int
    name: str
    eso_class: str
    type: str
    availability: str
    locations: List[str]
    description: str
    author: Optional[str] = None
    added_by: Optional[str] = None
    added_time: Optional[str] = None
    guild: Optional[int] = None
    emoji: Optional[str] = None

    @classmethod
    def from_database(cls, build: tuple) -> Build | None:
        id_, build_data = build
        return cls(
            id=id_,
            name=build_data['name'],
            eso_class=build_data['eso_class'],
            type=build_data['type'],
            availability=build_data['availability'],
            locations=build_data['locations'],
            description=build_data['description'],
            author=build_data.get('author'),
            added_by=build_data.get('added_by'),
            added_time=build_data.get('added_time'),
            guild=build_data.get('guild'),
            emoji=build_data.get('emoji'),
        )

    @property
    def to_database(self) -> dict:
        return self.to_json

    @property
    def to_json(self) -> dict:
        # return {
        #     'name': self.name,
        #     'eso_class': self.eso_class,
        #     'type': self.type,
        #     'availability': self.availability,
        #     'locations': self.locations,
        #     'description': self.description,
        #     'author': self.author,
        #     'added_by': self.added_by,
        #     'guild': self.guild,
        #     'emoji': self.emoji,
        # }
        return self.__dict__


if __name__ == '__main__':
    build = Build(
        id=1000,
        name="Vitalik",
        eso_class="Sorcerer",
        type="stam",
        availability="guild only",
        locations="Cyrodiil",
        description="Ohuenny bild",
    )

    print(build.to_json)
    print("----------------")
    print(build.__dict__)
