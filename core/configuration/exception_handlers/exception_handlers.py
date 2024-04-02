"""
Initialising Exception Handlers module.
GET OUT OF HERE!
"""
from dataclasses import dataclass

from fastapi import FastAPI


@dataclass(frozen=True)
class ExceptionHandlers:
    """
    Basic Exception Handlers class.
    To initialise ur exception handlers add it to __init__ file.
    """

    exception_handlers: tuple

    def register_exception_handlers(self, app: FastAPI):
        """
        Register all given exception handlers function.
        """

        for exception, exception_handler in self.exception_handlers:
            app.add_exception_handler(
                exception,
                exception_handler
            )
