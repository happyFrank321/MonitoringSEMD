from .middlewares import Middlewares
from app.internal.middlewares import request_log
from app.internal.middlewares import timeout
from app.internal.middlewares import trustedhost

__middlewares__ = Middlewares(
    middlewares=(
        # insert your middlewares here
        timeout.middleware,
        trustedhost.middleware,
        request_log.middleware
    )
)
