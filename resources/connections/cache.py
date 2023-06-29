from typing import overload

import json



class SongCache:

    data: dict[str, int]
    path: str = 'database/cache.json'
        
    @classmethod
    def add(cls, reference: str, song_id: int) -> None:
        with open(cls.path) as f:
            data = json.load(f)
        data[reference] = song_id
        with open(cls.path, 'w') as f:
            json.dump(data, f, indent=4)

    @classmethod
    def registered(cls, reference: str) -> bool:
        with open(cls.path) as f:
            return reference in json.load(f)

    @overload
    @classmethod
    def load(cls, reference: str) -> int:
        ...

    @overload
    @classmethod
    def load(cls, reference: None = None) -> dict[str, int]:
        ...

    @classmethod
    def load(cls, reference: str | None = None):
        with open(cls.path) as f:
            if reference:
                return json.load(f)[reference]
            else:
                return json.load(f)
            

class ReminderCache:
    
    data: dict[str, list[int]]
    path: str = 'database/reminders.json'
        
    @classmethod
    def add(cls, person_id: int, song_id: int) -> None:
        with open(cls.path) as f:
            data = json.load(f)
        if str(person_id) not in data:
            data[str(person_id)] = []
        data[str(person_id)].append(song_id)
        with open(cls.path, 'w') as f:
            json.dump(data, f, indent=4)

    @classmethod
    def load(cls, person_id: int) -> list[int]:
        with open(cls.path) as f:
            return json.load(f)[str(person_id)]