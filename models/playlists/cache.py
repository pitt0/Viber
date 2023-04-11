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
                'select playlists.rowid, playlist_title '
                'from playlists '
                'left join playlist_owners on playlists.rowid = playlist_id '
                'where playlist_title like :title and '
                'case when privacy = 0 then owner_id = :auth and :auth = :t_id '
                'else target_id = :t_id or owner_id = :auth end;'
            )
            params = {'title': f'%{input}%', 'auth': author.id, 't_id': target.id}
            cursor.execute(query, params)
            return cursor.fetchall()
        
    @staticmethod
    def advices(interaction: discord.Interaction, input: str = '%') -> list[tuple[int, str]]:
        with Connection() as cursor:
            query = (
                'select songs.rowid, song_title '
                'from playlist_songs '
                'inner join playlists on playlists.rowid = palylist_songs.playlist_id '
                'inner join songs on songs.rowid = playlist_songs.song_id '
                "where playlist_title = 'Advices' and playlists.target_id = ? "
                'and song_title like ?;'
            )
            cursor.execute(query, (interaction.user.id, input))
            return cursor.fetchall()
        
    @staticmethod
    def favourites(interaction: discord.Interaction, input: str = '%') -> list[tuple[int, str]]:
        with Connection() as cursor:
            query = (
                'select songs.rowid, song_title '
                'from playlist_songs '
                'inner join playlists on playlists.rowid = palylist_songs.playlist_id '
                'inner join songs on songs.rowid = playlist_songs.song_id '
                "where playlist_title = 'Liked' and playlists.target_id = ? "
                'and song_title like ?;'
            )
            cursor.execute(query, (interaction.user.id, input))
            return cursor.fetchall()