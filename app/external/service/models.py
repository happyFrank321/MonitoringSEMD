from typing import Optional, List

from pydantic import BaseModel


class MSEInfoRequest(BaseModel):
    id: int


class SemdInfo(BaseModel):
    event_id: int
    client_id: int
    doc_oid: int
    template_id: int
    semd_name: str
    semd_code: str
    date_start: str
    person_id: Optional[int] = None
    action_id: Optional[int] = None
    error_description: Optional[str] = None


class SemdInsertModel(SemdInfo):
    id: Optional[int] = None
    status_semd: Optional[int] = 0
    # remd_id: Optional[int] = None
    # result_remd = None
    # remd_status = None
    # date_create = None
    # date_accept = None
    sign: Optional[int] = 0
    sign_mo: Optional[int] = 0
    # ???
    # iemk_error = None
    # iemk_status = None
    # iemk_doc = None
    # sign_iemk = None
    # sign_iemk_mo = None