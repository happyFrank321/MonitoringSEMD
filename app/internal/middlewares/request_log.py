"""
Base middleware request log module.
GET OUT OF HERE!
"""
from time import perf_counter

from fastapi import Request
from fastapi import Response
from starlette.concurrency import iterate_in_threadpool

from ..exception_handlers.main_exception import base_exception_handler
from app.internal.middlewares.utils import BaseHTTPMiddleware
from core.logger import Logger
try:
    from settings import app_config
except ImportError:
    from settings_example import app_config


class RequestLog(BaseHTTPMiddleware):
    """
    Response spent time counter middleware.
    """

    async def dispatch(self, request: Request, call_next):
        _start_time = perf_counter()
        try:
            if not app_config.DEVELOPMENT:
                for route in app_config.banned_routes:
                    if route in str(request.url):
                        return Response(status_code=401)
            response = await call_next(request)
        except Exception as e:
            spent_time = perf_counter() - _start_time
            return await base_exception_handler(
                request, e, spent_time=spent_time
            )
        spent_time = perf_counter() - _start_time

        response_body = [chunk async for chunk in response.body_iterator]
        response.body_iterator = iterate_in_threadpool(iter(response_body))
        if len(response_body):
            try:
                response_body = response_body[0].decode()
            except:
                response_body = None

        Logger().info(
            f'User: [{request.client.host}:{request.client.port}]\n' +
            f'Request: [{request.url}]\n' +
            f'Response status: [{response.status_code}]\n' +
            f'Response time: [{spent_time:.5f}s]' +
            (f'\nResponse body:\n{response_body}'
             if app_config.DEVELOPMENT and response_body else ''
             )
        )

        return response


middleware = RequestLog
