from os import getpid
from os import kill
from signal import SIGTERM
from threading import Thread
from time import sleep
from typing import Any
from typing import Dict
from typing import List

from gunicorn.arbiter import Arbiter
from uvicorn.main import Server
from uvicorn.workers import UvicornWorker

from core.logger import Logger

try:
    from settings import app_config
except ImportError:
    from settings_example import app_config


class ReloaderThread(Thread):
    def __init__(self, worker: UvicornWorker, sleep_interval: float = 1.0):
        super().__init__()
        self.daemon = True
        self._worker = worker
        self._interval = sleep_interval

    def run(self) -> None:
        logger = Logger()
        while True:
            if not self._worker.alive:
                logger.info(f'Stopping process {getpid()}.')
                self.server.should_exit = True
                self.server.force_exit = True
                kill(getpid(), SIGTERM)
            sleep(self._interval)


class ConfiguredUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {
        'log_level': 'trace'
        if str(app_config.logger_settings.cmd_level) in ('debug', 'trace')
        else str(app_config.logger_settings.cmd_level),
        'reload': True,
        'factory': True
    }

    def __init__(self, *args: List[Any], **kwargs: Dict[str, Any]):
        super().__init__(*args, **kwargs)
        self._reloader_thread = ReloaderThread(self)

    async def _serve(self) -> None:
        self.config.app = self.wsgi
        self.server = Server(config=self.config)
        self._install_sigquit_handler()
        await self.server.serve(sockets=self.sockets)
        if not self.server.started:
            exit(Arbiter.WORKER_BOOT_ERROR)

    def run(self) -> None:
        if self.cfg.reload:
            self._reloader_thread.start()
        super().run()
