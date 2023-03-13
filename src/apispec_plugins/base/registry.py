from __future__ import annotations

from typing import TypeVar

__all__ = (
    "RegistryMixin",
    "RegistryError",
)

T = TypeVar("T")


class RegistryMixin:

    _registry: dict[str, T] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry[cls.__name__] = cls

    @classmethod
    def get_registry(cls):
        return cls._registry

    @classmethod
    def get_cls(cls, classname: str) -> T:
        try:
            return cls._registry[classname]
        except KeyError as error:
            raise RegistryError(
                f"Class with name {classname!r} was not found. You may need "
                "to import the class."
            ) from error


class RegistryError(NameError):
    """Raised on every class registry error, for instance,
    when a class lookup does not find the class.
    """
