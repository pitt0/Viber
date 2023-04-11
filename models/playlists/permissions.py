from dataclasses import dataclass
from enum import Enum

import discord


__all__ = ('Owner', 'PermissionLevel')


class PermissionLevel(Enum):
    Private = 0
    Viewable = 1
    Addable = 2
    Removeable = 3
    Admin = 4

@dataclass
class Owner:
    user: discord.User
    permission: PermissionLevel

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, discord.abc.Snowflake):
            return self.user.id == __o.id
        elif isinstance(__o, self.__class__):
            return self.user == __o.user
        return False