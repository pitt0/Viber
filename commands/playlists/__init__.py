from .advices import Advices
from .favourites import Favourites
from .playlist import Playlists
from discord.ext import commands


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Advices())
    await bot.add_cog(Favourites())
    await bot.add_cog(Playlists())