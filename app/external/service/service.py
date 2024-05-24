import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

import itertools

import httpx
from sqlalchemy import select, String, insert

from core.database import CConnection
from core.logger import logger, Logger
from core.models.models import Action, Event, ActionType, RbPrintTemplate, Client, RbIEMKDocument, EventType, \
    GetStatusTable2
from .child_services.Vista3Service import SemdService
from .models import MSEInfoRequest, SemdInfo, SemdInsertModel

from sqlalchemy.ext.asyncio.session import AsyncSession

__all__ = ['MonitoringService']

from ..Utils import prepare_result


class MonitoringService:
    """
    Клиентская часть.
    Класс для взаимодействия с Федеральным реестром больных туберкулёзом (ФРБТ)
    """

    def __init__(
            self
    ):
        self.SemdService = SemdService()
        # тут мы ставим ограничение, чтобы не занять все коннеты к базе или висте3
        self.semaphore = asyncio.Semaphore(8)


    async def get_mse_info(
            self,
            data: MSEInfoRequest
    ):
        return await self.SemdService.get_mse_info(data)

    async def collect_semd_action_info(
            self,
            start_date: datetime,
            end_date: datetime

    ) -> List[SemdInfo]:
        """
        Получение списка СЭМДов для проверки их формирования по Action
        """
        async with CConnection().get_session() as session:
            semds_result = await session.execute(
                select(
                    Action.id.label('action_id'),
                    Action.begDate.cast(String).label('date_start'),
                    Action.event_id.label('event_id'),
                    Action.person_id.label('person_id'),
                    Event.client_id.label('client_id'),
                    RbIEMKDocument.EGISZ_code.label('doc_oid'),
                    RbPrintTemplate.id.label('template_id'),
                    RbIEMKDocument.name.label('semd_name'),
                    RbIEMKDocument.code.label('semd_code')
                )
                .select_from(Action)
                .outerjoin(
                    ActionType,
                    ActionType.id == Action.actionType_id
                )
                .outerjoin(
                    RbPrintTemplate,
                    RbPrintTemplate.context == ActionType.context
                )
                .outerjoin(
                    RbIEMKDocument,
                    RbIEMKDocument.id == RbPrintTemplate.documentType_id
                )
                .outerjoin(
                    Event,
                    Event.id == Action.event_id
                )
                .outerjoin(
                    Client,
                    Client.id == Event.client_id
                )
                .where(
                    Action.deleted == 0,
                    Action.begDate >= start_date,
                    Action.begDate <= end_date,
                    Action.status == 2,  # Берем только закоченные
                    Event.deleted == 0,
                    ActionType.deleted == 0,
                    Client.deleted == 0,
                    RbPrintTemplate.deleted == 0,
                    ActionType.deleted == 0,
                    RbIEMKDocument.type == 'xml',
                    ~RbIEMKDocument.code.like('%SMS%')  # Берем только СЭМДы
                )
            )
            semds = semds_result.fetchall()

        return prepare_result(semds, SemdInfo)

    async def collect_semd_event_info(
            self,
            start_date: datetime,
            end_date: datetime
    ) -> List[SemdInfo]:
        """
        Получение списка СЭМДов для проверки их формирования по Event
        """
        async with CConnection().get_session() as session:
            semds_result = await session.execute(
                select(
                    Event.execDate.cast(String).label('date_start'),
                    Event.id.label('event_id'),
                    Event.execPerson_id.label('person_id'),
                    Event.client_id.label('client_id'),
                    RbIEMKDocument.EGISZ_code.label('doc_oid'),
                    RbPrintTemplate.id.label('template_id'),
                    RbIEMKDocument.name.label('semd_name'),
                    RbIEMKDocument.code.label('semd_code')
                )
                .select_from(RbIEMKDocument)
                .outerjoin(
                    RbPrintTemplate,
                    RbPrintTemplate.documentType_id == RbIEMKDocument.id
                )
                .outerjoin(
                    EventType,
                    EventType.context == RbPrintTemplate.context
                )
                .outerjoin(
                    Event,
                    Event.eventType_id == EventType.id
                )
                .outerjoin(
                    Client,
                    Client.id == Event.client_id
                )
                .where(
                    Event.execDate >= start_date,
                    Event.execDate <= end_date,
                    EventType.deleted == 0,
                    Event.execDate.isnot(None),  # Берем только закоченные
                    Event.deleted == 0,
                    Client.deleted == 0,
                    RbPrintTemplate.deleted == 0,
                    RbIEMKDocument.type == 'xml',
                    ~RbIEMKDocument.code.like('%SMS%')  # Берем только СЭМДы
                )
            )
            semds = semds_result.fetchall()

        return prepare_result(semds, SemdInfo)

    async def collect_semd_all_info(
            self,
            start_date: datetime = None,
            end_date: datetime = None,
    ):
        """
        Фнукция для получения массива СЭМДов для проверки их формирования
        """

        # Получаем список всех СЭМДов за определенное время
        results = await asyncio.gather(
            self.collect_semd_action_info(start_date, end_date),
            self.collect_semd_event_info(start_date, end_date)
        )
        result = list(itertools.chain.from_iterable(results))
        Logger().info(f'total results: {len(result)}')
        return result

    async def insert_semd_all_info(self, semd_list: List[SemdInfo]):

        tasks = [self.process_semd_data(semd) for semd in semd_list]

        for task in asyncio.as_completed(tasks):
            await task

    async def process_semd_data(self, data: SemdInfo):

        async with self.semaphore:
            response = await self.SemdService.get_semd_info(data)
            response = await self.insert_semd_info(SemdInsertModel(**response))
            return response

    async def insert_semd_info(self, data: SemdInsertModel):

        existing_data = await self.check_semd_exist(data)

        if not existing_data.id:
            query = insert(GetStatusTable2).values(**existing_data.dict())
            await CConnection().execute_stmt(query)
        return True

    async def check_semd_exist(self, data: SemdInsertModel):
        """
        Проверка на существование записи в БД
        """
        query = select(
            GetStatusTable2.id
        ) \
            .select_from(
            GetStatusTable2
        ) \
            .where(
            GetStatusTable2.event_id == data.event_id,
            GetStatusTable2.person_id == data.person_id,
            GetStatusTable2.client_id == data.client_id,
            GetStatusTable2.doc_oid == data.doc_oid,
            GetStatusTable2.template_id == data.template_id,
            GetStatusTable2.semd_name == data.semd_name,
            GetStatusTable2.semd_code == data.semd_code,
            GetStatusTable2.action_id == data.action_id,
        )
        result = await CConnection().get_value(query)
        data.id = result if result else None
        return data


    async def main_scrypt(
            self,
            start_date: datetime = None,
            end_date: datetime = None,
    ):
        semd_list = await self.collect_semd_all_info(start_date, end_date)
        return await self.insert_semd_all_info(semd_list)


