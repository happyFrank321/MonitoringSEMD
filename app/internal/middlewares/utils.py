from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware as StarletteBaseHTTPMiddleware


class BaseHTTPMiddleware(StarletteBaseHTTPMiddleware):
    """
    Base HTTP Middleware to prevent event dispatch.
    """
    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        except RuntimeError as exc:
            if str(exc) == 'No response returned.':
                request = Request(scope, receive=receive)
                if await request.is_disconnected():
                    return
            elif str(exc) == 'Event loop is closed':
                return
            print(f"{exc=}")
            # raise exc

    async def dispatch(self, request, call_next):
        """
        Subclasses should implement this.
        """
        raise NotImplementedError()
