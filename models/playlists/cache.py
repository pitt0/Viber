import discord

from resources import Connection


__all__ = ("CachedPlaylist",)



class CachedPlaylist:

    @staticmethod
    def load(interaction: discord.Interaction, input: str = '%') -> list[tuple[int, str]]:
        target = interaction.guild or interaction.user
        author = interaction.user
        with Connection() as cursor:
            query = (
                'select rowid, playlist_title '
                'from playlists left join playlist_owners on playlists.rowid = playlist_id '
                'where playlist_title like %:title% and '
                'case when privacy = 0 then owner_id = :auth and :auth = :t_id '
                'else target_id = :t_id or owner_id = :auth;'
            )
            params = {'title': input, 'auth': author.id, 't_id': target.id}
            cursor.execute(query, params)
        return cursor.fetchall()