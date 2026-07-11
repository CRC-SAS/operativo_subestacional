
class FcstInvalidURL(Exception):
    """Raised when the age is outside the valid range (0-120)."""
    def __init__(self, model: str, trgt_date: str):
        message = f"La URL al pronóstico del modelo {model} para el {trgt_date} es inválida."
        super().__init__(message) # Call the base class constructor


class FcstNotFound(Exception):
    """Raised when the age is outside the valid range (0-120)."""
    def __init__(self, model: str, trgt_date: str):
        message = f"El pronóstico del modelo {model} para el {trgt_date} no se encontró."
        super().__init__(message) # Call the base class constructor


class FcstNotYetPublished(Exception):
    """Raised when the age is outside the valid range (0-120)."""
    def __init__(self, model: str, trgt_date: str):
        message = f"El pronóstico del modelo {model} para el {trgt_date} aún no ha sido publicado."
        super().__init__(message) # Call the base class constructor


class FcstFileIsEmpty(Exception):
    """Raised when the age is outside the valid range (0-120)."""
    def __init__(self, model: str, trgt_date: str):
        message = f"El archivo con el pronóstico del modelo {model} para el {trgt_date} no tiene datos."
        super().__init__(message) # Call the base class constructor
