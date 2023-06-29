import discord

from resources import Connection


__all__ = ("Cached",)



class Cached:

    @staticmethod
    def playlists(interaction: discord.Interaction, input: str = '%') -> list[tuple[int, str]]:
        target = interaction.guild or interaction.user
        author = interaction.user
        with Connection() as cursor:
            query = (
                'SELECT playlists.rowid, playlist_title '
                'FROM playlists '
                'LEFT JOIN playlist_owners ON playlists.rowid = playlist_id '
                'WHERE playlist_title LIKE :title AND '
                'CASE WHEN privacy = 0 THEN owner_id = :auth AND :auth = :t_id '
                'ELSE target_id = :t_id OR owner_id = :auth end;'
            )
            params = {'title': f'%{input}%', 'auth': author.id, 't_id': target.id}
            cursor.execute(query, params)
            return cursor.fetchall()
        
    @staticmethod
    def advices(interaction: discord.Interaction, input: str = '%') -> list[tuple[int, str]]:
        with Connection() as cursor:
            query = (
                'SELECT songs.rowid, song_title '
                'FROM playlist_songs '
                'INNER JOIN playlists ON playlists.rowid = palylist_songs.playlist_id '
                'INNER JOIN songs ON songs.rowid = playlist_songs.song_id '
                "WHERE playlist_title = 'Advices' AND playlists.target_id = ? "
                'AND song_title like ?;'
            )
            cursor.execute(query, (interaction.user.id, input))
            return cursor.fetchall()
        
    @staticmethod
    def favourites(interaction: discord.Interaction, input: str = '%') -> list[tuple[int, str]]:
        with Connection() as cursor:
            query = (
                'SELECT songs.rowid, song_title '
                'FROM playlist_songs '
                'INNER JOIN playlists ON playlists.rowid = palylist_songs.playlist_id '
                'INNER JOIN songs ON songs.rowid = playlist_songs.song_id '
                "WHERE playlist_title = 'Liked' AND playlists.target_id = ? "
                'AND song_title like ?;'
            )
            cursor.execute(query, (interaction.user.id, input))
            return cursor.fetchall()