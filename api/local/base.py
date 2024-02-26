from sqlite3 import Cursor
from typing import Literal

from api import Connection
from typings.data import *
from typings.providers import *

type TABLE = Literal["songs", "albums", "artists"]
type SONG_DATA = tuple[LocalID, str, str, NGExternalID]
type ALBUM_DATA = tuple[str, str, str, NGExternalID]
type ARTIST_DATA = tuple[str, NGExternalID | None]


__all__ = ("_API",)


class _API:

    _table: str | None
    _var_name: str | None

    def __init_subclass__(cls, table: TABLE | None = None, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        cls._table = table
        cls._var_name = table.removesuffix("s") if table else None

    @classmethod
    async def _get_raw_data(
        cls, data: str, *params, pool: str | None = None
    ) -> SONG_DATA | ALBUM_DATA | ARTIST_DATA:
        assert cls._table is not None and cls._var_name is not None
        with Connection() as cursor:
            if pool:
                cursor.execute(
                    f"SELECT {data} FROM {cls._table} LEFT JOIN data ON {cls._var_name}_id = data_id WHERE {cls._var_name} IN {pool};",
                    params,
                )
            else:
                cursor.execute(
                    f"SELECT {data} FROM {cls._table} LEFT JOIN data ON {cls._var_name}_id = data_id WHERE {cls._var_name} = ?;",
                    params,
                )
            return cursor.fetchone()

    @staticmethod
    def _get_local_id(
        cursor: Cursor, provider: NGExternalProvider, provider_id: NGExternalID
    ) -> LocalID | None:
        cursor.execute(
            f"SELECT data_id FROM data WHERE {provider}_id = ?;", (provider_id,)
        )
        return (cursor.fetchone() or [None])[0]

    # @staticmethod
    # def _get_external_ids(cursor: Cursor, provider: NGProvider, data_id: LocalID | NGExternalID) -> DataID:
    #     match provider:
    #         case 'local':
    #             cursor.execute('SELECT * FROM data WHERE data_id = ?;', (data_id,))
    #         case _:
    #             cursor.execute(f'SELECT * FROM data WHERE {provider}_id = ?;', (data_id,))
    #     return cursor.fetchone()

    @staticmethod
    def _update_provider_id(
        cursor: Cursor, provider: Provider, data_id: str, provider_id: str | int
    ) -> None:
        cursor.execute(
            f"UPDATE data SET {provider}_id = ? WHERE data_id = ?;",
            (provider_id, data_id),
        )
