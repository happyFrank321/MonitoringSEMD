"""
Initialising Events module.
GET OUT OF HERE!
"""
from dataclasses import dataclass

from fastapi import FastAPI


@dataclass(frozen=True)
class Events:
    """
    Basic Events class.
    To initialise ur event add it to __init__ file.
    """

    events: tuple

    def register_events(self, app: FastAPI):
        """
        Register all given events function.
        """

        for event_type, event in self.events:
            app.add_event_handler(event_type, event)
