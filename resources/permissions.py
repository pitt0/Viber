from enum import IntEnum

__all__ = ("Privacy", "PermissionLevel")


class PermissionLevel(IntEnum):
    Extern = 0
    CanView = 1
    CanAddSongs = 2
    CanRemoveSongs = 3
    Admin = 4


class Privacy(IntEnum):
    Private = 0
    Visible = 1
    Addable = 2
    Removable = 3
    Free = 4
