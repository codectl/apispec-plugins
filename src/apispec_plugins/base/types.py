from typing import Optional

try:
    from pydantic.dataclasses import dataclass
    from apispec_plugins.base import registry
    base = registry.RegistryMixin
except ImportError:
    from dataclasses import dataclass
    registry = None
    base = object


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
class HTTPResponse(base):
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
