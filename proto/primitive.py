import hashlib
import inspect
from typing import Self
from abc import abstractmethod, ABCMeta


class PrimitiveMeta(ABCMeta):
    id: bytes

    def __str__(cls):
        return f"{cls.__qualname__}${hex(int.from_bytes(cls.id))[2:2 + 8]}{inspect.signature(cls.__init__)}"


class Primitive(metaclass=PrimitiveMeta):
    id: bytes

    @abstractmethod
    def serialize(self) -> bytes:
        """Serialize this primitive to bytes."""

    @classmethod
    @abstractmethod
    def deserialize(cls, data: bytes) -> Self:
        """Deserialize a primitive from bytes"""

    @classmethod
    @abstractmethod
    def measure(cls, data: bytes) -> int:
        """Measure length of the content to be read for deserialization"""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        cls.id = hashlib.sha256(kwargs.pop("id").encode()).digest()
