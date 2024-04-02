import logging
from logging.handlers import RotatingFileHandler
from logging import Logger as DefaultLogger

try:
    from settings import app_config, LoggerSetting
except ImportError:
    from settings_example import app_config, LoggerSetting


class Logger:
    _logger: DefaultLogger
    _logger_settings: LoggerSetting = app_config.logger_settings

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_logger') or cls._logger is None:
            cls._logger = logging.getLogger(__name__)
            cls._logger.propagate = False

            formatter = logging.Formatter('%(levelname)s %(asctime)s %(funcName)s %(message)s')

            file_handler = RotatingFileHandler(
                cls._logger_settings.file_path,
                mode='a',
                # 10 Мегабайт
                maxBytes=1000*1000*10,
                encoding='utf8',
                backupCount=1
            )
            file_handler.setFormatter(formatter)
            cls._logger.addHandler(file_handler)

            cls._logger.setLevel(logging.DEBUG if cls._logger_settings.VERBOSE_LOG else logging.INFO)

        return cls._logger
