from datetime import datetime, timedelta

from fastapi import APIRouter

from app.external.service.models import MSEInfoRequest
from app.external.service.service import MonitoringService

router = APIRouter(
    prefix='/vista3',
    tags=['Vista3 INFO'],
)

@router.get("/get_mse_info")
async def get_mse_info(mse_id: int):
    data = MSEInfoRequest(id=mse_id)
    return await MonitoringService().get_mse_info(data)


@router.get("/semd_info_list")
async def get_semd_info_list(
    period: int = 2,
    start_date: datetime = None,
    end_date: datetime = None,
):
    if not end_date:
        end_date = datetime.now() - timedelta(hours=16)  # TODO не забыть поменять время
    if not start_date:
        start_date = end_date - timedelta(hours=1)
    return await MonitoringService().main_scrypt(
        start_date=start_date,
        end_date=end_date
    )
