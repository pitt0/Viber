from dataclasses import dataclass
from enum import Enum

import discord


__all__ = ('Owner', 'PlaylistPermission')


class PlaylistPermission(Enum):
    Private = 0
    View = 1
    Add = 2
    Remove = 3
    Admin = 4

@dataclass
class Owner:
    user: discord.User
    permission: PlaylistPermission