import struct
import typing
from typing import Self, Collection

from .primitive import Primitive


class Int8(int, Primitive, id="integer8"):
    size = 1

    def serialize(self) -> bytes:
        return self.to_bytes(byteorder="little", signed=True)

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        return cls.from_bytes(data[: cls.size], byteorder="little", signed=True)

    @classmethod
    def measure(cls, data: bytes) -> int:
        return cls.size


class Int16(Int8, id="integer16"):
    size = 2

    def serialize(self) -> bytes:
        return self.to_bytes(2, byteorder="little", signed=True)


class Int32(Int8, id="integer32"):
    size = 4

    def serialize(self) -> bytes:
        return self.to_bytes(4, byteorder="little", signed=True)


class Int64(Int8, id="integer64"):
    size = 8

    def serialize(self) -> bytes:
        return self.to_bytes(8, byteorder="little", signed=True)


class UInt8(int, Primitive, id="unsigned-integer8"):
    size = 1

    def serialize(self) -> bytes:
        return self.to_bytes(byteorder="little")

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        return cls.from_bytes(data[: cls.size], byteorder="little")

    @classmethod
    def measure(cls, data: bytes) -> int:
        return cls.size


class UInt16(UInt8, id="unsigned-integer16"):
    size = 2

    def serialize(self) -> bytes:
        return self.to_bytes(2, byteorder="little")


class UInt32(UInt8, id="unsigned-integer32"):
    size = 4

    def serialize(self) -> bytes:
        return self.to_bytes(4, byteorder="little")


class UInt64(UInt8, id="unsigned-integer64"):
    size = 8

    def serialize(self) -> bytes:
        return self.to_bytes(8, byteorder="little")


class Boolean(int, Primitive, id="boolean"):
    size = 1

    def serialize(self) -> bytes:
        return self.to_bytes(byteorder="little")

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        return cls.from_bytes(data, byteorder="little")

    @classmethod
    def measure(cls, data: bytes) -> int:
        return cls.size

    def __str__(self):
        return "True" if self else "False"


class E(float, Primitive, id="e"):
    size = 2
    fmt = "<e"

    def serialize(self) -> bytes:
        return struct.pack(self.fmt, self)

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        return struct.unpack(cls.fmt, data[: cls.size])[0]

    @classmethod
    def measure(cls, data: bytes) -> int:
        return cls.size


class Float(E, id="float"):
    size = 4
    fmt = "<f"


class Double(E, id="double"):
    size = 8
    fmt = "<d"


class Char(str, Primitive, id="char"):
    def __init__(self, value: str) -> None:
        if not value:
            raise ValueError("Char cannot be empty")

    def serialize(self) -> bytes:
        return self[0].encode("utf8")

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        return cls(chr(data[0]))

    @classmethod
    def measure(cls, data: bytes) -> int:
        return 1


P = typing.TypeVar("P", bound=Primitive)

class Array(typing.Generic[P], list, Primitive, id="array"):
    if typing.TYPE_CHECKING:
        type: type[Primitive]

    def __class_getitem__(cls, type_) -> "Array":
        if not issubclass(type_, Primitive):
            raise TypeError("Array items must be Primitives")

        return typing.cast(
            Array,
            type(
                f"Array{type_.__qualname__}",
                (Array,),
                {"type": type_},
                id=f"array-{type_.__qualname__}",
            ),
        )

    def __init__(self, *items):
        if not hasattr(self, "type"):
            raise RuntimeError("Instantiating untyped array. Use Array[primitive](*items)")

        if len(items) == 1 and isinstance(items[0], typing.Iterable):
            items = items[0]

        items = list(items)

        for i, item in enumerate(items):
            if not isinstance(item, self.type):
                try:
                    items[i] = self.type(item)  # noqa
                except Exception as e:
                    raise TypeError(f"Invalid type of item: {self.type} expected, but got {type(item)}") from e

        super().__init__(items)

    def serialize(self) -> bytes:
        return UInt8(len(self)).serialize() + b"".join(map(self.type.serialize, self))  # type: ignore

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        data = data[:cls.measure(data)]
        length = UInt8.deserialize(data)

        items = []
        offset = UInt8.measure(data)
        for _ in range(length):
            items.append(cls.type.deserialize(data[offset:]))
            offset += cls.type.measure(data[offset:])

        return cls(items)

    @classmethod
    def measure(cls, data: bytes) -> int:
        length = UInt8.measure(data)

        items = UInt8.deserialize(data)

        for _ in range(items):
            length += cls.type.measure(data[length:])

        return length

    def copy(self) -> "Array":
        return type(self)(super().copy())

    def append(self, item: P):
        if not isinstance(item, self.type):
            try:
                item = self.type(item)  # noqa
            except Exception as e:
                raise TypeError(f"Invalid type of item: {self.type} expected, but got {type(item)}") from e

        super().append(item)

    def insert(self, index: int, item: P):
        if not isinstance(item, self.type):
            try:
                item = self.type(item)  # noqa
            except Exception as e:
                raise TypeError(f"Invalid type of item: {self.type} expected, but got {type(item)}") from e

        super().insert(index, item)

    def extend(self, iterable: typing.Iterable[P]):
        for item in iterable:
            if not isinstance(item, self.type):
                try:
                    item = self.type(item)  # noqa
                except Exception as e:
                    raise TypeError(f"Invalid type of item: {self.type} expected, but got {type(item)}") from e

            super().append(item)

    def pop(self, __index = -1) -> P:
        super().pop(__index)

    def __repr__(self):
        return "[{}]".format(", ".join(map(repr, self)))



class String(str, Primitive, id="string"):
    def serialize(self) -> bytes:
        encoded = self.encode("utf8")
        return len(encoded).to_bytes(2, byteorder="little") + encoded

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        return cls(data[2 : cls.measure(data)].decode("utf8"))

    @classmethod
    def measure(cls, data: bytes) -> int:
        return int.from_bytes(data[:2], byteorder="little") + 2
