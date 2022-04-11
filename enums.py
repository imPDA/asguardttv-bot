from enum import unique, Enum


@unique
class ResponseMode(Enum):
    OFF = 0
    MSG_ONLY = 1
    EMOJI_ONLY = 2
    ALL = 3

    