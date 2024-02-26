import json
from typing import overload

from models import LocalSong
from typings import LocalID


class SongCache:

    data: dict[str, LocalID]
    path: str = "database/cache/songs.json"

    @classmethod
    def add(cls, reference: str, song_id: str) -> None:
        with open(cls.path) as f:
            data = json.load(f)
        data[reference] = song_id
        with open(cls.path, "w") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def registered(cls, reference: str) -> bool:
        with open(cls.path) as f:
            return reference in json.load(f)

    @overload
    @classmethod
    def load(cls, reference: str) -> str | None: ...

    @overload
    @classmethod
    def load(cls, reference: None = None) -> dict[str, str]: ...

    @classmethod
    def load(cls, reference: str | None = None):
        with open(cls.path) as f:
            if reference:
                return json.load(f).get(reference)
            else:
                return json.load(f)


class ReminderCache:

    data: dict[str, list[str]]
    path: str = "database/cache/reminders.json"

    @classmethod
    def add(cls, person_id: int, song: LocalSong) -> None:
        with open(cls.path) as f:
            data = json.load(f)
        if str(person_id) not in data:
            data[str(person_id)] = []
        data[str(person_id)].append(song.id)
        with open(cls.path, "w") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def load(cls, person_id: int) -> list[str]:
        with open(cls.path) as f:
            return json.load(f).get(str(person_id), [])

    @classmethod
    def remove_first(cls, person_id: int) -> None:
        with open(cls.path) as f:
            data = json.load(f)
        data[str(person_id)].pop()
        with open(cls.path, "w") as f:
            json.dump(data, f, indent=4)
