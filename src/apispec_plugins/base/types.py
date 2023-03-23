from dataclasses import dataclass
from typing import Optional

from apispec_plugins.base.mixin import DataclassSchemaMixin


__all__ = (
    "AuthSchemes",
    "HTTPResponse",
    "Server",
    "Tag",
)


class AuthSchemes:
    @dataclass
    class BasicAuth:
        type: str = "http"
        scheme: str = "basic"


@dataclass
class HTTPResponse(DataclassSchemaMixin):
    code: int
    description: Optional[str] = None


@dataclass
class Server:
    url: str
    description: Optional[str] = None


@dataclass
class Tag:
    name: str
    description: Optional[str] = None
