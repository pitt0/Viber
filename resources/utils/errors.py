class LockingError(BaseException):
    """Raised when someone tries to lock a private playlist or to unlock a non-private playlist"""

class RenameError(BaseException):
    """Raised when someone tries to rename a non owned playlist"""

class OwnershipError(BaseException):
    pass

class NotASong(BaseException):
    pass