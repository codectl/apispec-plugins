from typing import Optional

from apispec_plugins.base.mixin import RegistryMixin
from pydantic import BaseModel


class Pet(BaseModel, RegistryMixin):
    id: Optional[int]
    name: str
