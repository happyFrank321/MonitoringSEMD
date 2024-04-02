"""
Basic startup module.
GET OUT OF HERE!
"""
import datetime
import multiprocessing
import sys

try:
    from uvicorn import run as uvicorn_run
except ImportError:
    sys.exit('Just install requirements dude...')

try:
    from settings import app_config
except ImportError:
    from settings_example import app_config

start_time = datetime.datetime.now()


if __name__ == '__main__':
    import logging

    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
    from core.logger import Logger
    _logger = Logger()
    try:
        from gunicorn.app.wsgiapp import run as gunicorn_run
    except ImportError:
        gunicorn_run = None

    if gunicorn_run and not app_config.DEVELOPMENT:
        _logger.critical('Start as Gunicorn application')

        def number_of_workers():
            app_workers = app_config.workers
            if isinstance(app_workers, int) and app_workers > 0:
                return app_workers
            return (multiprocessing.cpu_count() * 2) + 1

        options = {
            'bind': f"{app_config.host}:{app_config.port}",
            'workers': number_of_workers(),
            'log-level': 'debug'
            if app_config.logger_settings.VERBOSE_LOG
            else 'info',
            'reload-engine': 'poll',
            'preload': True,
            'worker-class': 'core.configuration.workers.ConfiguredUvicornWorker',
            'timeout': app_config.timeout
        }
        args = [sys.argv[0], "core:app"]
        for k, v in options.items():
            args.append(f"--{k}")
            args.append(str(v)) if not isinstance(v, bool) else 1
        sys.argv = args
        sys.orig_argv = args
        gunicorn_run()

    else:
        _logger.critical('Start as Uvicorn application')
        uvicorn_run(
            "core:app",
            host=app_config.host,
            port=app_config.port,
            log_level='trace'
            if app_config.logger_settings.VERBOSE_LOG
            else 'info',
            reload=app_config.DEVELOPMENT,
            factory=True
        )
