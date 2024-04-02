import asyncio
from typing import Dict, List

import httpx
from httpx import Response
from pydantic import BaseModel

from app.external.Utils import prepare_request_values
from app.external.service.models import MSEInfoRequest, SemdInfo
from core.logger import Logger

try:
    from settings import app_config
except ImportError:
    from settings_example import app_config


class SemdService:
    """
    Класс для взаимодействия с vista3
    """

    def __init__(
            self
    ):
        self.url = app_config.semd_config.url

    @staticmethod
    async def send_request(url: str, method: str, params=None, json_data=None):
        """
        Используем чтобы прокинуть запросы в vista3
        """
        async with httpx.AsyncClient(timeout=60) as client:
            params = prepare_request_values(params)
            json_data = prepare_request_values(json_data)
            response = await client.request(method.upper(), url, params=params, json=json_data)
        return response.json()

    @staticmethod
    async def send_requests_in_chunks(url: str, method: str, params=None, json_data=None,
                                      chunk_size: int = 10, max_concurrent: int = 10, max_retries: int = 3):
        """
        Пусть по умолчанию будет 4 одновременных запроса, чтобы не занимать всех воркеров (обычно их 15)
        """

        params = prepare_request_values(params)
        json_data = prepare_request_values(json_data)

        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_chunk(data, retry=0):
            if retry > max_retries:
                return None
            async with semaphore:
                async with httpx.AsyncClient(timeout=300) as client:
                    try:
                        response = await client.request(method.upper(), url, params=params, json=data)
                        data = response.content
                        return response.json()
                    except httpx.RemoteProtocolError as e:
                        Logger().info(f"Request failed. Retrying... (retry {retry}/{max_retries})")
                        return await send_chunk(data, retry=retry + 1)
                    except httpx.ReadTimeout as e:
                        Logger().info(f"Request timed out. Retrying... (retry {retry}/{max_retries})")
                        return await send_chunk(data, retry=retry + 1)

        return await asyncio.gather(*[send_chunk(data) for data in json_data])

    async def get_semd_info(self, data: SemdInfo):
        # TODO  python3 -m gunicorn --reload --bind 0.0.0.0:5050 --log-level debug -w 15 -k gevent --max-requests 1000 --timeout 240 application:app
        # Переделать запуск висты 3 на гуник, ОБЯЗАТЕЛЬНО таймаут, а то воркеры падают
        postfix = '/semd_infoV2'
        return await self.send_request(self.url + postfix, method='POST', json_data=data)

    async def get_mse_info(self, data: MSEInfoRequest) -> Dict:
        """
        Получение информации о МСЭ
        """
        postfix = '/mse'
        return await self.send_request(self.url + postfix, method='GET', params=data)


