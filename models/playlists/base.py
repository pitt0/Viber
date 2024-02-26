import calendar

import dateutil.parser as dparser

from resources import Privacy

__all__ = ("Playlist",)


class Playlist:

    def __init__(
        self,
        playlist_id: str,
        title: str,
        guild_id: int,
        author_id: int,
        creation_date: str,
        privacy: int,
    ) -> None:
        self.id = playlist_id
        self.title = title
        self.guild_id = guild_id
        self.author_id = author_id
        self._creation_date = dparser.parse(creation_date)
        self.privacy = Privacy(privacy)

    @property
    def created_on(self) -> str:
        return self._creation_date.strftime("%d/%m/%y")

    @property
    def date(self) -> str:
        # NOTE D is long day (April 10, 2023), d is short (10/4/2023)
        return f"<t:{calendar.timegm(self._creation_date.timetuple())}:d>"


# class Base(Paginator[Song]):

#     __client: discord.Client

#     def __init__(self, id: int, title: str, target: discord.User | discord.Guild, author: discord.User, creation_date: datetime.datetime, privacy: PermissionLevel) -> None:
#         self.id = id
#         self.title = title
#         self.target = target
#         self.author = author
#         self.creation_date = creation_date
#         self.privacy = privacy


#     def empty_embed(self) -> discord.Embed:
#         return super().empty_embed().set_author(name=f'Created by {self.author.display_name}', icon_url=self.author.display_avatar)

#     def paginate(self, index: int) -> discord.Embed:
#         _e = discord.Embed(
#             title=self.title,
#             description=f"by {self.author.display_name}",
#             colour=discord.Colour.blurple()
#         )
#         _e.set_footer(text=f"Page {index} of {self.pages}")
#         _e.set_author(name=f'Created by {self.author.display_name}', icon_url=self.author.display_avatar)

#         return _e

#     def embeds(self) -> list[discord.Embed]:
#         return super().embeds(lambda song: song.as_field)


#     async def dump(self, interaction: discord.Interaction) -> None:
#         ...

#     @classmethod
#     async def load(cls, interaction: discord.Interaction, id: int = MISSING, title: str = MISSING, target_id: int = MISSING) -> Self:
#         ...
