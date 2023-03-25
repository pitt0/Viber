import sqlite3 as sql



class Connection:

    def __init__(self) -> None:
        self.database = sql.connect("database/music.sqlite")

    def __enter__(self) -> sql.Cursor:
        return self.database.cursor()

    def __exit__(self, *args) -> None:
        self.database.commit()
        self.database.close()