import json
import sqlite3 as sql
from typing import Any

__all__ = ("Connection", "JSONConnection")


class Connection:

    def __init__(self) -> None:
        self.database = sql.connect("database/music.sqlite")

    def __enter__(self) -> sql.Cursor:
        cursor = self.database.cursor()
        return cursor.execute("PRAGMA foreign_keys = ON;")

    def __exit__(self, *_) -> None:
        self.database.commit()
        self.database.close()


class JSONConnection:

    folder: str = "database/"

    cache: Any

    def __init__(self, file: str) -> None:
        self.path = self.folder + file

    def __enter__(self):
        with open(self.path) as f:
            self.cache = json.load(f)
            return self.cache

    def __exit__(self, *_):
        with open(self.path, "w") as f:
            json.dump(self.cache, f, indent=4)
