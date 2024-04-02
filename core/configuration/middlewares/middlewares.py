"""
Initialising Middlewares module.
GET OUT OF HERE!
"""
from dataclasses import dataclass

from fastapi import FastAPI


@dataclass(frozen=True)
class Middlewares:
    """
    Basic Middlewares class.
    To initialise ur middleware add it to __init__ file.
    """

    middlewares: tuple

    def register_middlewares(self, app: FastAPI):
        """
        Register all given middlewares function.
        """

        for middleware in self.middlewares:
            app.add_middleware(middleware)
