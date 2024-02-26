from enum import Enum, auto
from pathlib import Path


class DataSearch(Enum):
    NotFound = auto()
    DataEmpty = auto()
    FoundName = auto()
    Found = auto()


def read_query(path: str) -> str:
    return Path(path).read_text()
