"""
Base middleware timeout module.
GET OUT OF HERE!
"""
from asyncio import TimeoutError as AsyncTimeoutError
from asyncio import wait_for

from fastapi import Request
from fastapi.responses import JSONResponse

from .utils import BaseHTTPMiddleware

try:
    from settings import app_config
except ImportError:
    from settings_example import app_config


class Timeout(BaseHTTPMiddleware):
    """
    Response spent time counter middleware.
    """

    async def dispatch(self, request: Request, call_next):
        _timeout = app_config.timeout
        if _timeout and isinstance(_timeout, int | float):
            try:
                return await wait_for(
                    call_next(request), timeout=_timeout
                )
            except AsyncTimeoutError:
                return JSONResponse(
                    {
                        'detail': f'Request processing time exceeded limit {_timeout} seconds.'
                    },
                    504
                )
        else:
            return await call_next(request)


middleware = Timeout
