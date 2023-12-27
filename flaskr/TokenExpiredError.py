class TokenExpiredError(Exception):
    """Exception raised when the token has expired."""

    def __init__(self, message="Token has expired. Please login again."):
        self.message = message
        super().__init__(self.message)