class SearchingException(Exception):
    name: str

class NotFound(SearchingException):
    """Exception raised when no song is found."""

    def __init__(self, *args):
        super().__init__(*args)
        self.name = "Could not find anything :c"

class WrongLink(SearchingException):
    """Exception raised when a url led to nothing."""

    def __init__(self, *args):
        super().__init__(*args)
        self.name = "Link returned no result"

class BadRequest(SearchingException):
    """Exception raised when someone uses a non-supported url."""

    def __init__(self, *args):
        super().__init__(*args)
        self.name = "Bad Request"