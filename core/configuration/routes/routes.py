"""
Initialising Routes module.
GET OUT OF HERE!
"""
from dataclasses import dataclass

from fastapi import FastAPI


@dataclass(frozen=True)
class Routes:
    """
    Basic Routes class.
    To initialise ur router add it to __init__ file.
    """

    routers: tuple

    def register_routes(self, app: FastAPI):
        """
        Register all given routes function.
        """

        for router in self.routers:
            app.include_router(router)
