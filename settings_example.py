"""
Settings for Vista FastAPI server backend module.
"""

from dataclasses import dataclass, field
import typing as t


# ----------------------------DB PART----------------------------


@dataclass(frozen=True)
class BaseSQLConfig:
    """
    :param port: Порт для подключения к SQL БД
    :param host: Адрес SQL БД
    :param schema: Название схемы (example: s11)
    :param user: Пользователь SQL БД
    :param password: Пароль от пользователя SQL БД
    :param connector: Коннектор для подключения к SQL БД (example: mysql+aiomysql)
    :param echo: Флаг для отправки запросов в консоль
    """
    schema: str
    port: int = 3306
    host: str = "192.168.1.3"
    user: str = "dbuser"
    password: str = "dbpassword"
    connector: str = "mysql+aiomysql"
    echo: bool = False


@dataclass(frozen=True)
class S11Config(BaseSQLConfig):
    schema: str = "p122vm"


@dataclass(frozen=True)
class LoggerConfig(BaseSQLConfig):
    schema: str = "logger"


@dataclass(frozen=True)
class KLADRConfig(BaseSQLConfig):
    schema: str = "kladr"


@dataclass(frozen=True)
class BaseNoSQLConfig:
    """
    :param port: Порт для подключения к NoSQL БД
    :param host: Адрес NoSQL БД
    :param schema: Номер схемы (example: "0")
    """
    port: int
    host: str
    schema: str


@dataclass(frozen=True)
class RedisConfig(BaseNoSQLConfig):
    port: int = 6379
    host: str = "example"
    schema: str = "0"


# ----------------------------Service PART----------------------------

@dataclass(frozen=True)
class SemdServiceConfig:
    url: str = "http://localhost:5050"

# ----------------------------Application PART----------------------------


@dataclass(frozen=False)
class BaseLoggerSettings:
    """
    :param VERBOSE_LOG: Подробный лог
    :param file_path: Путь к файлу с логгами
    """
    VERBOSE_LOG: bool
    file_path: str


@dataclass(frozen=False)
class BaseAppSettings:
    """
    :param DEVELOPMENT: Тестирование или бой
    :param host: Адрес сервиса
    :param port: Порт сервиса
    :param timeout: таймаут
    :param workers: Количество воркеров приложения
    :param trusted_hosts: Доверенные адресы для мидлваре
    :param trusted_hosts: Адресы, которые доступны только из тестового режима (DEVELOPMENT=True)
    :param logger_settings: Настройки логгера
    :param s11_db_config: Данные для подключения к боевой БД
    :param logger_db_config: Данные для подключения к БД логгера
    :param kladr_db_config: Данные для подключения к БД кладр
    :param redis_config:
    """
    DEVELOPMENT: bool
    host: str
    port: int
    timeout: int
    workers: int
    trusted_hosts: t.Tuple[str]
    banned_routes: t.Tuple[str]
    logger_settings: BaseLoggerSettings = field(init=False)
    s11_db_config: BaseSQLConfig
    logger_db_config: BaseSQLConfig
    kladr_db_config: BaseSQLConfig
    redis_config: BaseNoSQLConfig


@dataclass(frozen=False)
class LoggerSetting(BaseLoggerSettings):
    VERBOSE_LOG: bool = True
    file_path: str = 'log.log'


@dataclass(frozen=False)
class AppSettings(BaseAppSettings):
    """
    Настройки FASTApi приложения
    """
    DEVELOPMENT: bool = True
    host: str = '0.0.0.0'
    port: int = 5055
    timeout: int = 0
    workers: int = 0
    trusted_hosts: t.Tuple[str] = (
        r'.*',
        # r'127\.0\.0\.1',
        # r'localhost',
        # r'10\..*',
        # r'192\.168\..*',
        # r'172\..*'
    )
    banned_routes: t.Tuple[str] = tuple([])
    logger_settings: BaseLoggerSettings = field(init=False)
    s11_db_config: BaseSQLConfig = S11Config()
    logger_db_config: BaseSQLConfig = LoggerConfig()
    kladr_db_config: BaseSQLConfig = KLADRConfig()
    redis_config: BaseNoSQLConfig = RedisConfig()
    semd_address = SemdServiceConfig()

    def __post_init__(self):
        # self.banned_routes = ['/admin/'] if not self.DEVELOPMENT else []
        logger_settings = LoggerSetting()
        if self.DEVELOPMENT:
            logger_settings.cmd_level = 'debug'
            logger_settings.file_level = 'debug'
        self.logger_settings = logger_settings


app_config = AppSettings()
# INIT YOUR SERVICE CONFIG HERE!
service_config = None
