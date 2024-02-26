from typing import Callable

import discord

from resources import PermissionLevel

type Cache = list[tuple[str, str]]
type LiveCache = Callable[[discord.Interaction, str, PermissionLevel], Cache]
