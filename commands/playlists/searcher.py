import discord

import ui
from api.cache import SongCache
from api.local import SongsAPI as SongsAPI
from api.web import SongsAPI as WebSongsAPI
from models import ExternalSong, LocalSong
from resources import Time


class SongSearcher:

    async def choose_song(
        self, interaction: discord.Interaction, query: str, choices: list[ExternalSong]
    ) -> LocalSong:
        view = ui.Selector(choices)
        await interaction.followup.send(embed=choices[0].embed, view=view)
        await view.wait()
        return await SongsAPI.upload(view.song, query)

    async def _search_song(
        self, interaction: discord.Interaction, query: str, choose: bool
    ) -> LocalSong:
        if query.startswith("http"):
            print(f"[{Time.now()}] Url found, loading.")
            if (song := await WebSongsAPI.load(query)) is None:
                print(f"[{Time.now()}] Url returned nothing, raising Exception.")
                raise ValueError
            print(f"[{Time.now()}] Song found, exiting.")
            return await SongsAPI.upload(song)

        if choose:
            print(f"[{Time.now()}] User set flag choose.")
            if (choices := await WebSongsAPI.search(query)) is None:
                raise ValueError
            print(
                f'[{Time.now()}] Searching "{query}" returned {len(choices)} results.'
            )
            print(f"[{Time.now()}] Letting user choose song.")
            return await self.choose_song(interaction, query, choices)

        else:
            print(f"[{Time.now()}] Skipping choice step.")
            if (song_id := SongCache.load(query)) is not None:
                print(
                    f'[{Time.now()}] "{query}" is present in the cache, loading from database.'
                )
                return await SongsAPI.get_song(song_id)

            else:
                print(
                    f'[{Time.now()}] "{query}" is not present in the database, searching.'
                )
                if (song := await WebSongsAPI.search(query, 1)) is None:
                    raise ValueError
                print(f"[{Time.now()}] Song found, continuing.")
                return await SongsAPI.upload(song[0])
