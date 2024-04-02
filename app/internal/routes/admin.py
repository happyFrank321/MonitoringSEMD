import inspect
from asyncio import sleep as asleep

from fastapi import APIRouter
from sqlalchemy import Result

from core.database import CConnection
from core.database import prepare_result
from core.errors import DatabaseException
from core.logger import Logger

try:
    import settings
except ImportError:
    import settings_example as settings


router = APIRouter(
    prefix='/admin',
    tags=['Admin'],
    include_in_schema=settings.app_config.DEVELOPMENT
)


@router.get('/get_config')
async def get_config():
    """
    Admin get config from server
    """
    all_attributes = dir(settings)

    # Filter out the variables
    variables = {
        attr: getattr(settings, attr)
        for attr in all_attributes
        if not callable(getattr(settings, attr))
        and not inspect.ismodule(getattr(settings, attr))
        and not attr.startswith("_")
    }

    return {
        'response': variables
    }


@router.get('/test_db_connection')
async def test_db_connection():
    """
    Admin test inited database connection
    """

    return {
        'response': 'Connection is ready!!'
        if await CConnection().is_ready()
        else 'Connection ERROR'
    }


@router.get('/test_get_table')
async def test_get_table(table: str, columns: int = 10):
    """
    Admin test get table from inited database
    """

    return {
        'response': await prepare_result(
            await CConnection().get_records(
                f'SELECT * FROM {table} ' +
                (f'LIMIT {columns}' if columns else '')
            )
        )
    }


@router.get('/test_get_value')
async def test_get_value():
    """
    Admin test get value from table with where search.
    """

    resp = await CConnection().get_values(
        f'''
        SELECT a.id, a.event_id, a.person_id, rbi.EGISZ_code, rbt.id, rbi.name
        FROM Action a
        INNER JOIN ActionType at ON at.id = a.actionType_id
        INNER JOIN rbPrintTemplate rbt ON rbt.context = at.context
        INNER JOIN rbIEMKDocument rbi ON rbi.id = rbt.documentType_id
        where a.createDatetime >= '2023-10-10'
          and a.modifyDatetime >= '2023-10-10'
          and rbt.documentType_id
        '''
    )
    return {'response': f"{resp}"}


@router.get('/test_get_values')
async def test_get_values(table: str, filter: str = None, column: str = None):
    """
    Admin test get values from table with where search.
    """

    return {
        'response': await prepare_result(
            await CConnection().get_values(
                f"SELECT * FROM {table} " +
                (f"WHERE {column} = '{filter}'" if filter and column else '')
            )
        )
    }


@router.get('/test_get_record')
async def test_get_record(table: str, filter: str = None, column: str = None):
    """
    Admin test get record from table with where search.
    """

    return {
        'response': await prepare_result(
            await CConnection().get_record(
                f"SELECT * FROM {table} " +
                (f"WHERE {column} = '{filter}'" if filter and column else '')
            )
        )
    }


@router.get('/test_get_records')
async def test_get_records(table: str, filter: str = None, column: str = None):
    """
    Admin test get records from table with where search.
    """

    return {
        'response': await prepare_result(
            await CConnection().get_records(
                f"SELECT * FROM {table} " +
                (f"WHERE {column} = '{filter}'" if filter and column else '')
            )
        )
    }


@router.get('/test_query_with_response')
async def test_query_with_response(query: str):
    """
    Admin test custom db query with response.
    """

    return {
        'response':
            await prepare_result(
                await CConnection().get_records(
                    query
                )
            )
    }


@router.get('/test_query_without_response')
async def test_query_without_response(query: str):
    """
    Admin test custom db query with response.
    """

    return {
        'response': str(response)
        if isinstance(response := await CConnection().get_record(query), Result)
        or isinstance(response, DatabaseException)
        else f'Error: {response}'
    }


@router.get('/test_logger')
async def test_logger(log_msg: str = 'Default test log message'):
    """
    Admin test log message
    """

    _logger = Logger()
    _logger.debug(log_msg)
    return {
        'resp': 'true'
    }


@router.get('/test_simple_request')
async def test_simple_request():
    """
    Admin test simple request with no payload
    """

    return True


@router.get('/test_base_exception')
async def test_base_exception(exc_msg: str = 'Test Exception message'):
    """
    Admin test raise base Exception class exception
    """

    raise Exception(exc_msg)


@router.get('/test_sleep')
async def test_sleep(seconds: int):
    """
    Admin test sleep.
    """

    await asleep(seconds)

    return {
        'response': f'Slept {seconds} seconds.'
    }
