from .events import Events
from app.internal.events import dispose_db
from app.internal.events import logger

__events__ = Events(
    events=(
        # insert your events here
        logger.event_startup,  # Save startup log on last position. Insert events before this
        dispose_db.event_shutdown,
        logger.event_shutdown
    )
)
