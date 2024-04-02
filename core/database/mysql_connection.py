"""
Base Database connection module.
GET OUT OF HERE!
"""
from asyncio import sleep as asleep
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Type

from sqlalchemy import Result
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from core.errors import DatabaseException
from core.logger import Logger
from core.database.db_driver_abc import DbDriverABC

try:
    from settings import app_config, BaseSQLConfig
except ImportError:
    from settings_example import app_config, BaseSQLConfig

__all__ = ['CConnection']


class CConnection(DbDriverABC):
    """
    Base Database connection class.
    """

    def __init__(self, custom_engine=None):
        self.custom_engine = custom_engine
        self.__IS_READY_STATEMENT = text("SELECT 1")

        self._engine = create_async_engine(
            self.__prepare_connection_data(config=app_config.s11_db_config),
            hide_parameters=False,
            poolclass=NullPool,
            future=True,
            echo=app_config.DEVELOPMENT
        )
        self._session = async_sessionmaker(
            bind=self._engine if not self.custom_engine else self.custom_engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

    def __getattr__(self, name: str):
        return getattr(self._session, name)

    async def is_ready(self) -> bool:
        try:
            async with self.get_session() as session:
                await session.execute(self.__IS_READY_STATEMENT)
            return True

        except Exception as err:
            Logger().error(err)
            return False

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator:
        """
        Base Database async session.
        """

        try:
            async with self._session() as session:
                yield session
        except Exception as exc:
            await session.rollback()
            raise exc
        finally:
            await session.close()

    async def get_value(
        self,
        stmt
    ):
        """
        Base Database get first value from select.
        """

        result = await self.execute_stmt(stmt)
        if isinstance(result, Result):
            _r = result.scalars().first()
            result.close()
            return _r
        return result

    async def get_values(
        self,
        stmt
    ):
        """
        Base Database get all value from select.
        """

        result = await self.execute_stmt(stmt)
        if isinstance(result, Result):
            _r = result.scalars().all()
            result.close()
            return _r
        return result

    async def get_record(
        self,
        stmt
    ):
        """
        Base Database get first record from select.
        """

        result = await self.execute_stmt(stmt)
        if isinstance(result, Result):
            _r = result.first()
            result.close()
            return _r
        return result

    async def get_record_join(
        self,
        stmt
    ):
        """
        Base Database get first record from select.
        """

        result = await self.execute_stmt(stmt)
        if isinstance(result, Result):
            _r = result.first()
            result.close()
            return _r[0]
        return result

    async def get_records(
        self,
        stmt
    ):
        """
        Base Database get all records from select.
        """

        result = await self.execute_stmt(stmt)
        if isinstance(result, Result):
            _r = result.all()
            result.close()
            return _r
        return result

    async def execute_stmt(
        self,
        stmt
    ):
        """
        Base Database execute statement.
        :warning: Don't forget to close session!
        """

        async with self.get_session() as session:
            if isinstance(stmt, str):
                stmt = text(stmt)
            try:
                result = await session.execute(stmt)
                await session.commit()
                return result
            except OperationalError:
                await asleep(0.2)
                return await self.execute_stmt(stmt)
            except (
                ProgrammingError, DatabaseError
            ) as error:
                return DatabaseException(
                    str(error.__cause__)[1:-1].replace('\"', '')
                )

    async def insert_or_update_stmt(
        self,
        stmt
    ):
        """
        Base Database execute statement.
        :warning: Don't forget to close session!
        """

        return await self.execute_stmt(stmt)

    @staticmethod
    def __prepare_connection_data(config: BaseSQLConfig):
        """
        Base hidden prepare connection type.
        """

        return f"{config.connector}://{config.user}:{config.password}@{config.host}:{config.port}/{config.schema}"
