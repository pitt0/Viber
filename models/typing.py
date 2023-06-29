import discord

from typing import TypedDict


class Field(TypedDict):
    name: str
    value: str | int
    inline: bool


GUILD_ID = int
USER = discord.User | discord.Member