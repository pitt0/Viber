import discord

from api import Connection
from resources import PermissionLevel
from typings import Cache

__all__ = ("Cached",)


class Cached:

    @staticmethod
    def songs(_, input: str = "%", *__) -> Cache:
        with Connection() as cursor:
            query = (
                "SELECT s.song_id, s.song_title | 'by' | a.artist_name "
                "FROM songs s "
                "JOIN ( "
                "SELECT sal.data_id, sal.artist_id "
                "FROM ( "
                "SELECT sa.data_id, sa.artist_id, ROW_NUMBER() OVER (PARTITION BY sa.data_id) AS row_num "
                "FROM authors sa "
                ") AS sal "
                "WHERE sal.row_num = 1 "
                ") AS sa ON s.song_id = sa.data_id "
                "JOIN artists a ON sa.artist_id = a.artist_id;"
            )
            cursor.execute(query, (input,))
            return cursor.fetchall()

    @staticmethod
    def playlists(
        interaction: discord.Interaction,
        input: str = "%",
        permission_level: PermissionLevel = PermissionLevel.CanView,
    ) -> Cache:
        guild = interaction.guild or interaction.user
        author = interaction.user
        with Connection() as cursor:
            query = (
                "SELECT playlist_id, playlist_title FROM playlists "
                "LEFT JOIN playlist_owners ON playlist_owners.playlist_id = playlists.playlist_id "
                "WHERE playlist_title LIKE :title AND :g_id = guild_id AND (privacy > :p_lvl OR (:auth = owner_id AND permission_lvl >= :p_lvl));"
            )
            params = {
                "title": f"%{input}%",
                "auth": author.id,
                "g_id": guild.id,
                "p_lvl": permission_level.value,
            }
            cursor.execute(query, params)
            return list(set(cursor.fetchall()))

    @staticmethod
    def advices(interaction: discord.Interaction, input: str = "%", *_) -> Cache:
        with Connection() as cursor:
            query = (
                "SELECT song_id, song_title FROM playlist_songs "
                "INNER JOIN special ON special.playlist_id = palylist_songs.playlist_id "
                "INNER JOIN songs ON songs.song_id = playlist_songs.song_id "
                "WHERE playlist_type = 'Advices' AND user_id = ? "
                "AND song_title like ?;"
            )
            cursor.execute(query, (interaction.user.id, input))
            return cursor.fetchall()

    @staticmethod
    def favourites(interaction: discord.Interaction, input: str = "%", *_) -> Cache:
        with Connection() as cursor:
            query = (
                "SELECT song_id, song_title FROM playlist_songs "
                "INNER JOIN special ON special.playlist_id = palylist_songs.playlist_id "
                "INNER JOIN songs ON songs.song_id = playlist_songs.song_id "
                "WHERE playlist_type = 'Favourites' AND user_id = ? "
                "AND song_title like ?;"
            )
            cursor.execute(query, (interaction.user.id, input))
            return cursor.fetchall()
