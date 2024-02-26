from typing import Callable, Coroutine

import discord
from discord import app_commands as slash

from resources import PermissionLevel
from typings import LiveCache

Autocomplete = Callable[
    [discord.Interaction, str], Coroutine[None, None, list[slash.Choice[str]]]
]


def autocomplete(
    cache: LiveCache, permission_level: PermissionLevel = PermissionLevel.CanView
) -> Autocomplete:

    async def load_cache(
        interaction: discord.Interaction, current: str
    ) -> list[slash.Choice[str]]:
        return [
            slash.Choice(name=playlist[1], value=playlist[0])
            for playlist in cache(interaction, current, permission_level)
        ]

    return load_cache
