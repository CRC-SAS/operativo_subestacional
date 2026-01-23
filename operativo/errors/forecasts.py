
class FcstNotFound(Exception):
    """Raised when the age is outside the valid range (0-120)."""
    def __init__(self, model: str, trgt_date: str):
        message = f"The forecast for model {model} for {trgt_date} was not found."
        super().__init__(message) # Call the base class constructor


class FcstNotYetPublished(Exception):
    """Raised when the age is outside the valid range (0-120)."""
    def __init__(self, model: str, trgt_date: str):
        message = f"The forecast for model {model} for {trgt_date} has not yet been published."
        super().__init__(message) # Call the base class constructor
