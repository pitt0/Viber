from sqlite3 import Cursor

from api import Connection
from api.utils import DataSearch, read_query
from models import Album, ExternalAlbum
from resources import Maybe
from typings import LocalID, NGExternalProvider

__all__ = ("AlbumsAPI",)


def album_query(query: str) -> str:
    return read_query("sql/albums/" + query)


class AlbumsAPI:

    @staticmethod
    async def get_album(
        album_id: LocalID, provider: NGExternalProvider = "spotify"
    ) -> Maybe[Album]:
        with Connection() as cursor:
            query = album_query("get_data.sql")
            cursor.execute(
                query,
                (
                    f"{provider}_id",
                    album_id,
                ),
            )
        return Maybe(Album(*cursor.fetchone(), _ext_provider=provider))

    @staticmethod
    def _is_present(cursor: Cursor, album: ExternalAlbum) -> DataSearch:
        registered = cursor.execute(
            album_query("exists.sql"),
            (
                f"{album.provider}_id",
                f"album_name='{album.name}'",
            ),
        ).fetchone()
        if registered is None:
            return DataSearch.NotFound

        if len(registered) > 0:
            return DataSearch.Found

        return DataSearch.FoundName

    @classmethod
    async def upload_album(cls, album: ExternalAlbum) -> Album:
        # TODO: add artists
        with Connection() as cursor:

            match cls._is_present(cursor, album):
                case DataSearch.NotFound:
                    query = album_query("add.sql")
                    cursor.executemany(
                        query, (album.name, album.release_date, album.thumbnail)
                    )

                    (album_id,) = cursor.execute(
                        album_query("get_id.sql"), (album.name,)
                    ).fetchone()

                    query = album_query(f"update_{album.provider}_id.sql")
                    cursor.execute(query, (album.id, album.name))

                case DataSearch.DataEmpty:
                    # Uncertain if it was found or not: there is no actual match in the `data` table but there are also some missing data
                    query = f"SELECT FROM albums LEFT JOIN data ON album_id = data_id WHERE album_name = ? AND {album.provider}_id = NULL;"
                    cursor.execute(query, (album.name))
                    # TODO: Try to retrieve other provider ids and check those
                    raise NotImplementedError

                case DataSearch.FoundName:
                    # check the number of present albums
                    query = "SELECT COUNT(*) FROM albums;"
                    cursor.execute(query)
                    (n,) = cursor.fetchone()
                    # create the album's local id based on how many albums are there
                    # NOTE: the trigger will update the value anyways, but it will insert the same value, so it doesn't really matter
                    album_id = f"a{n+1}"
                    query = "INSERT INTO albums VALUES (?, ?, ?, ?);"
                    cursor.execute(
                        query,
                        (album_id, album.name, album.release_date, album.thumbnail),
                    )

                case DataSearch.Found:
                    album_id = cls._get_local_id(cursor, album.provider, album.id)
                    assert (
                        album_id is not None
                    ), "`_is_present` returned `DataSearch.Found`, but local_id is `None`"

        return (await cls.get_album(album_id, album.provider)).unwrap()
