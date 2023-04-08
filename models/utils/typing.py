from typing import TypedDict

import discord


class Field(TypedDict):
    name: str
    value: str | int
    inline: bool


GUILD_ID = int
USER = discord.User | discord.Member