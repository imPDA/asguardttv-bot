from __future__ import annotations
from enums import ResponseMode
from typing import Any
from dataclasses import dataclass


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

    def to_json(self) -> dict:
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

