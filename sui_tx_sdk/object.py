# Copyright (c) JubiterWallet
# Author: Ruquan
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
import base64
from .bcs import Deserializer, Serializer
from .account_address import AccountAddress
from .sui_address import SuiAddress


class ObjectID:
    value: AccountAddress

    def __init__(self, address: AccountAddress):
        self.value = address

    def __eq__(self, o: ObjectID) -> bool:
        return self.value == o.value

    def __str__(self) -> str:
        return self.value.__str__()

    @staticmethod
    def from_hex(address: str) -> ObjectID:
        return ObjectID(AccountAddress.from_hex(address))

    @staticmethod
    def deserialize(deserializer: Deserializer) -> ObjectID:
        return ObjectID(deserializer.struct(AccountAddress))

    def serialize(self, serializer: Serializer):
        serializer.struct(self.value)


class ObjectDigest:
    LENGTH: int = 32
    value: bytes

    def __init__(self, digest: bytes):
        if not len(digest) == ObjectDigest.LENGTH:
            raise Exception(f"Expected digest of length 32, get {len(digest)}")

        self.value = digest

    def __eq__(self, o: ObjectDigest) -> bool:
        return self.value == o.value

    def __str__(self) -> str:
        return f"0x{self.value.hex()}"

    @staticmethod
    def from_base64(b64: str) -> ObjectDigest:
        digest = base64.b64decode(b64)
        return ObjectDigest(digest)

    @staticmethod
    def deserialize(deserializer: Deserializer) -> ObjectDigest:
        return ObjectDigest(deserializer.bytes())

    def serialize(self, serializer: Serializer):
        serializer.bytes(self.value)


class ObjectRef:
    object_id: ObjectID
    sequence_number: int
    object_digest: ObjectDigest

    def __init__(
        self, object_id: ObjectID, sequence_number: int, object_digest: ObjectDigest
    ):
        self.object_id = object_id
        self.sequence_number = sequence_number
        self.object_digest = object_digest

    def __eq__(self, o: ObjectRef) -> bool:
        return (
            self.object_id == o.object_id
            and self.sequence_number == o.sequence_number
            and self.object_digest == o.object_digest
        )

    def __display__(self) -> str:
        return (
            f"Object ID : {self.object_id}\n"
            f"Sequence Number : {self.sequence_number:#x}\n"
            f"Object Digest : {self.object_digest.value.hex()}"
        )

    @staticmethod
    def deserialize(deserializer: Deserializer) -> ObjectRef:
        object_id = deserializer.struct(ObjectID)
        sequence_number = deserializer.u64()
        object_digest = deserializer.struct(ObjectDigest)
        return ObjectRef(object_id, sequence_number, object_digest)

    def serialize(self, serializer: Serializer):
        serializer.struct(self.object_id)
        serializer.u64(self.sequence_number)
        serializer.struct(self.object_digest)
