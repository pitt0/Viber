import json

from typing import Any



class JSONConnection:

    folder: str = 'database/'

    cache: Any

    def __init__(self, file: str) -> None:
        self.path = self.folder + file

    def __enter__(self):
        with open(self.path) as f:
            self.cache = json.load(f)
            return self.cache
        
    def __exit__(self, *args):
        with open(self.path, 'w') as f:
            json.dump(self.cache, f, indent=4)