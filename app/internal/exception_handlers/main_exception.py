"""
Base exception handler main exception module.
GET OUT OF HERE!
"""
from traceback import format_exc

from fastapi.utils import is_body_allowed_for_status_code
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.responses import Response

from core.logger import Logger


async def base_exception_handler(
    request: Request,
    exc: Exception,
    spent_time=None
) -> Response:
    """
    Base http exception handler.
    """

    headers = getattr(exc, "headers", None)
    status_code = getattr(exc, 'status_code', 500)

    Logger().exception(
        f'User: [{request.client.host}:{request.client.port}]\n'
        f'Request: [{request.url}]\n'
        f'Response: [{status_code}]\n' +
        (f'Response time: {spent_time:.5f}s\n' if spent_time else '') +
        f'Exception: {format_exc()}'
    )

    if not is_body_allowed_for_status_code(status_code):
        return Response(
            status_code=status_code,
            headers=headers
        )
    return PlainTextResponse(
        f'User: [{request.client.host}:{request.client.port}]\n\n'
        f'Request: [{request.url}]\n\n'
        f'Response: [{status_code}]\n\n' +
        (f'Response time: {(spent_time):.5f}s\n\n' if spent_time else '') +
        f'Exception: {format_exc()}',
        status_code=status_code,
        headers=headers
    )


exception_handler = (Exception, base_exception_handler)
