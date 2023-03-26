try:
    from pydantic.dataclasses import dataclass
except ImportError:
    from dataclasses import dataclass
from typing import Optional

from apispec_plugins.base.mixin import DataclassSchemaMixin


__all__ = (
    "AuthSchemes",
    "Server",
    "Tag",
    "HTTPResponse",
)


class AuthSchemes:
    @dataclass
    class BasicAuth:
        type: str = "http"
        scheme: str = "basic"


@dataclass
class Server:
    url: str
    description: Optional[str] = None


@dataclass
class Tag:
    name: str
    description: Optional[str] = None


@dataclass
class HTTPResponse(DataclassSchemaMixin):
    code: int
    description: Optional[str] = None
