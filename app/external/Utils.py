import time
from functools import wraps
from typing import List

from pydantic import BaseModel


def prepare_result(data: List, model: BaseModel):
    return [model(**dict(row._mapping)) for row in data] if data else []


def prepare_request_values(data):
    if data is None:
        return None
    if isinstance(data, BaseModel):
        return data.dict() if data else None
    elif isinstance(data, list):
        return [data.dict() for data in data] if isinstance(data[0], BaseModel) else data
    elif isinstance(data, dict):
        return data
    else:
        raise ValueError("Unsupported json_data type")

