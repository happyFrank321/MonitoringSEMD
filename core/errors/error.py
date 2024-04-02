"""
Base Exceptions module.
"""
from core.logger import Logger


__all__ = ['DatabaseException', 'ConnectionException']


class DatabaseException(Exception):
    """
    Ошибка БД.
    """

    def __init__(self, message: str = '', exception: Exception = '') -> None:
        # TODO: FIX ME!
        self._message = message
        Logger().exception(f"{message=} | {exception=}")
        super().__init__(message, exception)


class ConnectionException(DatabaseException):
    """
    Ошибка подключения к БД.
    """

    def __init__(self, argument_required: str, exception: Exception) -> None:
        _message = f"Неправильно заполнено поделючение к бд: {argument_required}"
        super().__init__(_message, exception)
