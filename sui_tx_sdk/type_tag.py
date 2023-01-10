# Copyright (c) Aptos
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from .account_address import AccountAddress
from .bcs import Deserializer, Serializer


class TypeTag:
    """TypeTag represents a primitive in Move."""

    BOOL: int = 0
    U8: int = 1
    U64: int = 2
    U128: int = 3
    ADDRESS: int = 4
    SIGNER: int = 5
    VECTOR: int = 6
    STRUCT: int = 7

    value: typing.Any

    def __init__(self, value: typing.Any):
        self.value = value

    def __eq__(self, other: TypeTag) -> bool:
        return (
            self.value.variant() == other.value.variant() and self.value == other.value
        )

    def __str__(self):
        return self.value.__str__()

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def deserialize(deserializer: Deserializer) -> TypeTag:
        variant = deserializer.uleb128()
        if variant == TypeTag.BOOL:
            return TypeTag(BoolTag.deserialize(deserializer))
        elif variant == TypeTag.U8:
            return TypeTag(U8Tag.deserialize(deserializer))
        elif variant == TypeTag.U64:
            return TypeTag(U64Tag.deserialize(deserializer))
        elif variant == TypeTag.U128:
            return TypeTag(U128Tag.deserialize(deserializer))
        elif variant == TypeTag.ADDRESS:
            return TypeTag(AccountAddressTag.deserialize(deserializer))
        elif variant == TypeTag.SIGNER:
            raise NotImplementedError
        elif variant == TypeTag.VECTOR:
            raise NotImplementedError
        elif variant == TypeTag.STRUCT:
            return TypeTag(StructTag.deserialize(deserializer))
        raise NotImplementedError

    def serialize(self, serializer: Serializer):
        serializer.uleb128(self.value.variant())
        serializer.struct(self.value)


def simple_tag(tag: int, name: str):
    def decorate(cls):
        def deserialize(deserializer: Deserializer):
            return cls()

        def serialize(self, serializer: Serializer):
            return

        setattr(cls, "deserialize", deserialize)
        setattr(cls, "serialize", serialize)
        setattr(cls, "variant", lambda self: tag)
        setattr(cls, "__str__", lambda self: name)
        setattr(cls, "__eq__", lambda self, o: isinstance(o, cls))

        return cls

    return decorate


@simple_tag(TypeTag.BOOL, "bool")
class BoolTag:
    pass


@simple_tag(TypeTag.U8, "u8")
class U8Tag:
    pass


@simple_tag(TypeTag.U64, "u64")
class U64Tag:
    pass


@simple_tag(TypeTag.U128, "u128")
class U128Tag:
    pass


@simple_tag(TypeTag.ADDRESS, "address")
class AddressTag:
    pass


class StructTag:
    address: AccountAddress
    module: str
    name: str
    type_args: typing.List[TypeTag]

    def __init__(self, address, module, name, type_args):
        self.address = address
        self.module = module
        self.name = name
        self.type_args = type_args

    def __eq__(self, other: StructTag) -> bool:
        return (
            self.address == other.address
            and self.module == other.module
            and self.name == other.name
            and self.type_args == other.type_args
        )

    def __str__(self) -> str:
        value = f"{self.address}::{self.module}::{self.name}"
        if len(self.type_args) > 0:
            value += f"<{self.type_args[0]}"
            for type_arg in self.type_args[1:]:
                value += f", {type_arg}"
            value += ">"
        return value

    @staticmethod
    def from_str(type_tag: str) -> StructTag:
        name = ""
        index = 0
        while index < len(type_tag):
            letter = type_tag[index]
            index += 1

            if letter == "<":
                raise NotImplementedError
            else:
                name += letter

        split = name.split("::")
        return StructTag(AccountAddress.from_hex(split[0]), split[1], split[2], [])

    def variant(self):
        return TypeTag.STRUCT

    @staticmethod
    def deserialize(deserializer: Deserializer) -> StructTag:
        address = deserializer.struct(AccountAddress)
        module = deserializer.str()
        name = deserializer.str()
        type_args = deserializer.sequence(TypeTag.deserialize)
        return StructTag(address, module, name, type_args)

    def serialize(self, serializer: Serializer):
        serializer.struct(self.address)
        serializer.str(self.module)
        serializer.str(self.name)
        serializer.sequence(self.type_args, Serializer.struct)
