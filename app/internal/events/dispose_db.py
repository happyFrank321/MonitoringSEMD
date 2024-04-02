"""
Base event dispose database module.
GET OUT OF HERE!
"""
from core.database import CConnection
from core.logger import Logger


async def shutdown_dispose():
    await CConnection()._engine.dispose()
    Logger().critical('Database disposed.')


event_shutdown = ('shutdown', shutdown_dispose)
