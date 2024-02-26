import sqlite3 as sql


class Connection:

    def __init__(self) -> None:
        self.database = sql.connect("database/music.sqlite")

    def __enter__(self) -> sql.Cursor:
        cursor = self.database.cursor()
        return cursor.execute("PRAGMA foreign_keys = ON;")

    def __exit__(self, *_) -> None:
        self.database.commit()
        self.database.close()
