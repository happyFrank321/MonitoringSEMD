import datetime

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from main import start_time

try:
    from settings import app_config
except ImportError:
    from settings_example import app_config


router = APIRouter(
    tags=['Welcome'],
    include_in_schema=False
)


@router.get('/', include_in_schema=False)
async def main(request: Request):
    """
    Base service response on open page.
    """

    if app_config.DEVELOPMENT:
        _logger_cfg = app_config.logger_settings
        _db_cfg = app_config.s11_db_config

        _now = datetime.datetime.now()
        _delta = _now - start_time
        _days = _delta.days
        _hours = int(_delta.seconds // 3600)
        _minutes = int((_delta.seconds % 3600) // 60)
        _seconds = int((_delta.seconds % 3600) % 60)
        _ip = request.url.hostname

        _resp = HTMLResponse(status_code=200, content=f"""
            <html>
                <body>
                    <h1>[{_now}]</h1>
                    <h2>From last reload: {_days} days, {_hours} hours, {_minutes} minutes, {_seconds} seconds.</h2>
                    <h2>Server local IP address: {_ip}</h2>
                    <h2>Your IP Address: {request.client.host}</h2>
                    <h2>Database connection:</h2>
                    <details>
                        <summary></summary>
                        <p><h3>Host: {_db_cfg.host}</h3></p>
                        <p><h3>Port: {_db_cfg.port}</h3></p>
                        <p><h3>User: {_db_cfg.user}</h3></p>
                        <p><h3>Password: {_db_cfg.password}</h3></p>
                    </details>
                    <h2>Log level</h2>
                    <details>
                        <summary></summary>
                        <p><h3>Global: {'debug' if _logger_cfg.VERBOSE_LOG else 'info'}</h3></p>
                    </details>
                    <h2>Documentation and other service data</h2>
                        <h3><a href='http://{_ip}:{app_config.port}/docs'>Docs</a>
                            <a href='http://{_ip}:{app_config.port}/redoc'>Redoc</a></h3>
                </body>
            </html>
            """
        )
    else:
        _resp = RedirectResponse('/docs')

    return _resp


@router.get('/favicon.ico', include_in_schema=False)
async def favicon():
    """
    Base empty favicon response.
    """

    return FileResponse('app/internal/routes/favicon.ico')
