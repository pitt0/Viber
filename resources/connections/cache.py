from typing import overload

import json


class Cache:

    data: dict[str, str]
    path: str = 'database/cache.json'

    def __enter__(self) -> dict[str, str]:
        with open(self.path) as f:
            self.data = json.load(f)
            return self.data
        
    @classmethod
    def add(cls, reference: str, song_id: int) -> None:
        with open(cls.path) as f:
            data = json.load(f)
        data[reference] = song_id
        with open(cls.path, 'w') as f:
            json.dump(data, f, indent=4)
        
    def __exit__(self, *args) -> None:
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=4)

    @classmethod
    def registered(cls, reference: str) -> bool:
        with open(cls.path) as f:
            return reference in json.load(f)

    @overload
    @classmethod
    def load(cls, reference: str) -> str:
        ...

    @overload
    @classmethod
    def load(cls, reference: None = None) -> dict[str, str]:
        ...

    @classmethod
    def load(cls, reference: str | None = None):
        with open(cls.path) as f:
            if reference:
                return json.load(f)[reference]
            else:
                return json.load(f)