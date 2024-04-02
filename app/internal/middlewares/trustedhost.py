"""
Base middleware trust host module.
GET OUT OF HERE!
"""
import re

from fastapi import Request
from starlette.responses import PlainTextResponse

from .utils import BaseHTTPMiddleware

try:
    from settings import app_config
except ImportError:
    from settings_example import app_config


class TrustHost(BaseHTTPMiddleware):
    """
    Response trust host middleware.
    """

    async def dispatch(self, request: Request, call_next):
        is_valid_host = False

        trusted_hosts = app_config.trusted_hosts

        host = request.client.host

        if host is None:
            return await call_next(request)

        for pattern in trusted_hosts:
            if re.search(pattern, host):
                is_valid_host = True
                break

        if is_valid_host:
            return await call_next(request)

        return PlainTextResponse(
            f"Unauthorized host ({host})",
            status_code=401
        )


middleware = TrustHost
