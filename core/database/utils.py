"""
Base Database utils module.
"""
from typing import List
from typing import Sequence
from typing import Tuple

from sqlalchemy.engine.row import Row

from core.errors import DatabaseException
from core.logger import Logger


__all__ = ['prepare_result']


async def prepare_result(
        records):
    """
    Base prepare fetched result to List[Dict].
    Return DatabaseException if excepted an sqlalchemy Exception.
    Return Exception if excepted unexpected error.
    """

    if records:
        if isinstance(records, DatabaseException):
            return records
        try:
            if isinstance(records, list):
                return [row._asdict() for row in records]
        except AttributeError as a_e:
            try:
                if isinstance(records, Row):
                    return [records._asdict()]
            except Exception:
                if len(records) > 0 and isinstance(records, List | str | Tuple | Sequence):
                    return records
                err = DatabaseException('Невалидные данные', a_e)
                Logger().error(err)
                return err
        except Exception as e:
            err = Exception('Непредвиденная ошибка', e)
            Logger().error(err)
            return err
    elif isinstance(records, DatabaseException):
        return records
