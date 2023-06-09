import discord

from resources import MISSING
from resources.connections import Connection
from typing import Literal


def dump(provider_id: str, provider: Literal['local', 'spotify', 'youtube'], title: str, target_id: int, author_id: int, privacy: int = 1) -> int:
    with Connection() as cursor:
        query = (
            'insert into playlists (playlist_title, target_id, author_id, privacy) '
            'values (?, ?, ?, ?) returning rowid;'
        )
        cursor.execute(query, (title, target_id, author_id, privacy))
        rowid = cursor.fetchone()[0]

        if provider != 'local':
            cursor.execute(f'insert into external_playlist_ids (playlist_id, {provider}_id) values (?, ?);', (rowid, provider_id))

        cursor.execute('insert into playlist_owners (playlist_id, owner_id, permission_lvl) values (?, ?, 4);', (rowid, author_id))

        return rowid
    

def get(id: int = MISSING, title: str = MISSING, target: int = MISSING) -> tuple[int, str, int, int, str, int]:
    with Connection() as cursor:
        query = (
            'select rowid, playlist_title, target_id, author_id, creation_date, privacy '
            'from playlists '
            'where rowid = ? or (playlist_title = ? and target_id = ?);'
        )
        params = (id or None, title or None, target or None)

        cursor.execute(query, params)
        return cursor.fetchone()
    

# General queries
def songs(id: int) -> list[tuple[int]]:
    with Connection() as cursor:
        cursor.execute('select song_id from playlist_songs where playlist_id = ?;', (id,))
        return cursor.fetchall()


def owners(id: int) -> list[tuple[int, int]]:
    with Connection() as cursor:
        cursor.execute('select owner_id, permission_lvl from playlist_owners where playlist_id = ?;', (id,))
        return cursor.fetchall()


def add(playlist_id: int, song_id: int, user_id: int) -> None:
    with Connection() as cursor:
        # NOTE asserting song is already registered in database
        cursor.execute('insert into playlist_songs (playlist_id, song_id, added_by) values (?, ?, ?);', (playlist_id, song_id, user_id))


def remove(playlist_id: int, song_id: int) -> None:
    with Connection() as cursor:
        cursor.execute('delete from playlist_songs where playlist_id = ? and song_id = ?;', (playlist_id, song_id))


def rename(id: int, name: str) -> None:
    with Connection() as cursor:
        cursor.execute('update playlists set playlist_title = ? where rowid = ?;', (name, id))


def delete(id: int) -> None:
    with Connection() as cursor:
        cursor.execute('delete from playlists where rowid = ?;', (id,))
        cursor.execute('delete from playlist_songs where playlist_id = ?;', (id,))
        cursor.execute('delete from playlist_owners where playlist_id = ?;', (id,))

def check_existance(interaction: discord.Interaction, title: str) -> bool:
    target = interaction.guild or interaction.user
    with Connection() as cursor:
        cursor.execute('select 1 from playlists where target_id = ? and author_id = ? and playlist_title = ?;', (target.id, interaction.user.id, title))
        return bool(cursor.fetchone())
    
def check_ownership(id: int, user: discord.User) -> bool:
    with Connection() as cursor:
        cursor.execute('select 1 from playlist_owners where playlist_id = ? and owner_id = ?;', (id, user.id))
        return bool(cursor.fetchone())

def check_owner_level(id: int, user: discord.User) -> int:
    with Connection() as cursor:
        cursor.execute('select permission_lvl from playlist_owners where playlist_id = ? and owner_id = ?;', (id, user.id))
        return (cursor.fetchone() or [0])[0]
    
def set_ownership_lvl(**data) -> None:
    with Connection() as cursor:
        query = (
            'insert into playlist_owners (playlist_id, owner_id, permission_lvl) '
            'values (:pid, :oid, :plvl) '
            'on conflict do update '
            'set permission_lvl = :plvl;'
        )
        cursor.execute(query, data)

def set_privacy_level(id: int, pl: int) -> None:
    with Connection() as cursor:
        query = 'update playlists set privacy = ? where rowid = ?;'
        cursor.execute(query, (pl, id))