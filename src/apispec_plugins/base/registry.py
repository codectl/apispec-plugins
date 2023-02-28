from typing import TypeVar

from pydantic.main import ModelMetaclass

__all__ = (
    "RegistryBase",
    "PydanticRegistry",
    "RegistryError",
)

T = TypeVar("T")


class RegistryBase(type):

    _registry: dict[str, T] = {}

    def __new__(mcs, name, bases, attrs):
        cls = type.__new__(mcs, name, bases, attrs)
        mcs._registry[cls.__name__] = cls
        return cls

    @classmethod
    def get_registry(mcs):
        return mcs._registry

    @classmethod
    def get_cls(mcs, classname: str) -> T:
        try:
            return mcs._registry[classname]
        except KeyError as error:
            raise RegistryError(
                f"Class with name {classname!r} was not found. You may need "
                "to import the class."
            ) from error


class PydanticRegistry(ModelMetaclass, RegistryBase):
    """Harness registry metaclass for pydantic"""


class RegistryError(NameError):
    """Raised on every class registry error, for instance,
    when a class lookup does not find the class.
    """
