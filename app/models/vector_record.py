from pydantic import BaseModel
from typing import Any


class VectorRecord(BaseModel):
    id: str
    content: str
    metadata: dict[str, Any] = {}