from typing import Optional

from apispec_plugins.ext.pydantic import BaseModel


class Pet(BaseModel):
    id: Optional[int]
    name: str
