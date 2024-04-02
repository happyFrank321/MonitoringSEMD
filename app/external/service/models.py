from typing import Optional, List

from pydantic import BaseModel


class MSEInfoRequest(BaseModel):
    id: int


class SemdInfo(BaseModel):
    event_id: int
    person_id: int
    client_id: int
    doc_oid: int
    template_id: int
    semd_name: str
    semd_code: str
    date_start: str
    action_id: Optional[int] = None
    error_description: Optional[str] = None

