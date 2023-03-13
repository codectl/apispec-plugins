from dataclasses import dataclass


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
class HTTPResponse:
    code: int
    description: str


@dataclass
class Server:
    url: str
    description: str


@dataclass
class Tag:
    name: str
    description: str
