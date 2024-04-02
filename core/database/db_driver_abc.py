from abc import abstractmethod
from typing import Dict, Type, AsyncGenerator

from core.utils.app_dependencies_abc import AppDependenciesABC


class Singleton(type):
    _instances: Dict[Type, Dict[str, object]] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = {}
        key = str(args) + str(kwargs)
        if key not in cls._instances[cls]:
            cls._instances[cls][key] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls][key]


class DbDriverABC(AppDependenciesABC, metaclass=Singleton):
    @abstractmethod
    async def is_ready(self) -> bool:
        """Not Implemented"""

    @abstractmethod
    async def get_session(self) -> AsyncGenerator:
        """Not Implemented"""

    @abstractmethod
    def __prepare_connection_data(self, config):
        """Not Implemented"""

    @abstractmethod
    async def get_value(self, stmt):
        """Not Implemented"""

    @abstractmethod
    async def get_values(self, stmt):
        """Not Implemented"""

    @abstractmethod
    async def get_record(self, stmt):
        """Not Implemented"""

    @abstractmethod
    async def get_records(self, stmt):
        """Not Implemented"""

    @abstractmethod
    async def execute_stmt(self, stmt):
        """Not Implemented"""

    @abstractmethod
    async def insert_or_update_stmt(self, stmt):
        """Not Implemented"""
