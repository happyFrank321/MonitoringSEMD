"""
Base event logger module.
GET OUT OF HERE!
"""
from core.logger import Logger


async def startup_log():
    Logger().critical('Startup.')


async def shutdown_log():
    Logger().critical('Shutdown.')


event_startup = ('startup', startup_log)
event_shutdown = ('shutdown', shutdown_log)
