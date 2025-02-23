import typing
from abc import ABC

from .primitive import Primitive


class PrimitiveP(typing.Protocol):
    def __call__(self, python: typing.Any) -> Primitive: ...

    @classmethod
    def deserialize(cls, data: bytes) -> Primitive: ...

    @classmethod
    def measure(cls, data: bytes) -> int: ...


class ComplexType(Primitive, ABC, id="complex"):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)


class ComplexMappedType(ComplexType, ABC, id="complex-mapped"):
    if typing.TYPE_CHECKING:
        map: typing.Mapping[str, PrimitiveP]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    def serialize(self) -> bytes:
        if not hasattr(self, "map"):
            raise ValueError("ComplexMappedType requires a map")

        result = b""
        for attr, primitive in self.map.items():
            value = getattr(self, attr)

            if isinstance(value, Primitive):
                result += value.serialize()
                continue

            result += primitive(value).serialize()

        return result

    @classmethod
    def deserialize(cls, data: bytes) -> "ComplexMappedType":
        if not hasattr(cls, "map"):
            raise ValueError("ComplexMappedType requires a map")

        data = data[: cls.measure(data)]

        kwargs = {}

        offset = 0
        for attr, primitive in cls.map.items():
            kwargs[attr] = primitive.deserialize(data[offset:])
            offset += primitive.measure(data[offset:])

        return cls(**kwargs)

    @classmethod
    def measure(cls, data: bytes) -> int:
        if not hasattr(cls, "map"):
            raise ValueError("ComplexMappedType requires a map")

        length = 0
        for primitive in cls.map.values():
            length += primitive.measure(data[length:])

        return length


class ComplexDataType(ComplexMappedType, ABC, id="complex-data"):
    if typing.TYPE_CHECKING:
        map: dict[str, PrimitiveP]

    def __init__(self, **kwargs):
        for name in kwargs.copy():
            if name not in self.map:
                continue

            setattr(self, name, kwargs.pop(name))

        super().__init__(**kwargs)

    def __init_subclass__(cls, **kwargs):
        cls.map = {}

        for attr, primitive in cls.__annotations__.items():
            if issubclass(primitive, Primitive):
                cls.map[attr] = typing.cast(PrimitiveP, primitive)

        super().__init_subclass__(**kwargs)


    def __eq__(self, other: "ComplexMappedType") -> bool:
        if not isinstance(other, ComplexMappedType):
            return super().__eq__(other)

        for attr in self.map:
            if getattr(self, attr) != getattr(other, attr):
                return False

        return True


    def __repr__(self):
        qualname = type(self).__qualname__
        kwargs = {}
        for name in self.map.keys():
            kwargs[name] = getattr(self, name)

        return (
            qualname + "(" + ", ".join(f"{name}={value!r}" for name, value in kwargs.items()) + ")"
        )
