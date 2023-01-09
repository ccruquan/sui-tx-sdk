# Copyright (c) JubiterWallet
# Author: Ruquan
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from .bcs import Deserializer, Serializer
from .object import ObjectRef, ObjectID


class CallArg:
    PURE: int = 0
    OBJECT: int = 1
    OBJECT_VECTOR: int = 2

    variant: int
    value: ARG

    def __init__(self, arg: ARG):
        if isinstance(arg, PureArg):
            self.variant = 0
        elif isinstance(arg, ObjectArg):
            self.variant = 1
        elif isinstance(arg, list) and all(isinstance(x, ObjectArg) for x in arg):
            self.variant = 2
        else:
            raise TypeError
        self.value = arg

    def __eq__(self, o: CallArg) -> bool:
        return self.variant == o.variant and self.value == o.value

    def __str__(self) -> str:
        return self.value.__str__()

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def deserialize(deserializer: Deserializer) -> CallArg:
        variant = deserializer.uleb128()
        if variant == CallArg.PURE:
            arg = deserializer.struct(PureArg)
        elif variant == CallArg.OBJECT:
            arg = deserializer.struct(ObjectArg)
        elif variant == CallArg.OBJECT_VECTOR:
            arg = deserializer.sequence(ObjectArg.deserialize)
        else:
            raise TypeError
        return CallArg(arg)

    def serialize(self, serializer: Serializer):
        serializer.uleb128(self.variant)
        if self.variant == CallArg.OBJECT_VECTOR:
            serializer.sequence(self.value, Serializer.struct)
        else:
            serializer.struct(self.value)


class PureArg:
    value: bytes

    def __init__(self, v: bytes):
        self.value = v

    def __eq__(self, o: PureArg) -> bool:
        return self.value == o.value

    def __str__(self) -> str:
        return self.value.__str__()

    @staticmethod
    def deserialize(deserializer: Deserializer) -> PureArg:
        arg = deserializer.bytes()
        return PureArg(arg)

    def serialize(self, serializer: Serializer):
        serializer.bytes(self.value)


class ObjectArg:
    IMM_OR_OWNED_OBJECT: int = 0
    SHARED_OBJECT: int = 1

    variant: int
    value: ObjectRef | SharedObjectArg

    def __init__(self, obj: ObjectRef | SharedObjectArg):
        if isinstance(obj, ObjectRef):
            self.variant = ObjectArg.IMM_OR_OWNED_OBJECT
        elif isinstance(obj, SharedObjectArg):
            self.variant = ObjectArg.SHARED_OBJECT
        else:
            raise TypeError

        self.value = obj

    def __eq__(self, o: ObjectArg) -> bool:
        return self.variant == o.variant and self.value == o.value

    def __str__(self) -> str:
        return self.value.__str__()

    @staticmethod
    def deserialize(deserializer: Deserializer) -> ObjectArg:
        variant = deserializer.uleb128()
        if variant == ObjectArg.IMM_OR_OWNED_OBJECT:
            arg = deserializer.struct(ObjectRef)
        elif variant == ObjectArg.SHARED_OBJECT:
            arg = deserializer.struct(SharedObjectArg)
        else:
            raise TypeError

        return ObjectArg(arg)

    def serialize(self, serializer: Serializer):
        serializer.uleb128(self.variant)
        serializer.struct(self.value)


class SharedObjectArg:
    object_id: ObjectID
    initial_shared_version: int

    def __init__(self, object_id: ObjectID, version: int):
        self.object_id = object_id
        self.initial_shared_version = version

    def __eq__(self, o: SharedObjectArg) -> bool:
        return (
            self.object_id == o.object_id
            and self.initial_shared_version == o.initial_shared_version
        )

    def __str__(self) -> str:
        return f"{{id : {self.object_id}, version: {self.initial_shared_version}}}"

    @staticmethod
    def deserialize(deserializer: Deserializer) -> SharedObjectArg:
        object_id = deserializer.struct(ObjectID)
        version = deserializer.u64()
        return SharedObjectArg(object_id, version)

    def serialize(self, serializer: Serializer):
        serializer.struct(self.object_id)
        serializer.u64(self.initial_shared_version)


ARG = PureArg | ObjectArg | typing.List[ObjectArg]
