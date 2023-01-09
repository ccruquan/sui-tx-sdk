# Copyright (c) JubiterWallet
# Author: Ruquan
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
import typing
from base64 import b64encode, b64decode

from .bcs import Deserializer, Serializer
from .sui_address import SuiAddress
from .ed25519 import Ed25519Signature, Ed25519PublicKey, Ed25519KeyPair
from .secp256k1 import Secp256k1Signature, Secp256k1PublicKey, Secp256k1KeyPair


class SuiKeyPair:
    value: Ed25519KeyPair | Secp256k1KeyPair

    def __init__(self, kp: Ed25519KeyPair | Secp256k1KeyPair) -> None:
        if not isinstance(kp, (Ed25519KeyPair, Secp256k1KeyPair)):
            raise TypeError
        self.value = kp

    def __eq__(self, o: SuiKeyPair) -> bool:
        return self.value == o.value

    def public_key(self) -> PublicKey:
        return PublicKey(self.value.public_key())

    def base64(self) -> str:
        data = bytearray()
        data.append(self.public_key().scheme())
        data.extend(self.public_key().bytes())
        data.extend(self.value.private_key_bytes())
        return b64encode(data).decode("utf8")

    @staticmethod
    def from_base64(s: str) -> SuiKeyPair:
        data = b64decode(s)

        if data[0] == Ed25519PublicKey.SCHEME:
            return SuiKeyPair(
                Ed25519KeyPair.from_private_key(data[1 + Ed25519PublicKey.LENGTH :])
            )
        elif data[0] == Secp256k1PublicKey.SCHEME:
            return SuiKeyPair(
                Secp256k1KeyPair.from_private_key(data[1 + Secp256k1PublicKey.LENGTH :])
            )
        else:
            raise TypeError

    def sign(self, msg: bytes) -> Signature:
        sig = self.value.sign(msg)
        return Signature.from_public_signature(self.public_key(), sig)


Ed25519SuiPublicKey = typing.NewType("Ed25519SuiPublicKey", Ed25519PublicKey)
Secp256k1SuiPublicKey = typing.NewType("Secp256k1SuiPublicKey", Secp256k1PublicKey)

SuiPublicKey = Ed25519SuiPublicKey | Secp256k1SuiPublicKey


class PublicKey:
    value: Ed25519PublicKey | Secp256k1PublicKey

    def __init__(self, pk: Ed25519PublicKey | Secp256k1PublicKey) -> None:
        if not isinstance(pk, (Ed25519PublicKey, Secp256k1PublicKey)):
            raise TypeError
        self.value = pk

    def __eq__(self, o: PublicKey) -> bool:
        return self.value == o.value

    def scheme(self) -> int:
        return self.value.scheme()

    def bytes(self) -> bytes:
        return self.value.bytes()

    def base64(self) -> str:
        data = bytearray()
        data.append(self.scheme())
        data.extend(self.bytes())
        return b64encode(data).decode("utf8")

    @staticmethod
    def from_base64(s: str) -> PublicKey:
        data = b64decode(s)

        if data[0] == Ed25519PublicKey.SCHEME:
            return PublicKey(Ed25519PublicKey(data[1:]))
        elif data[0] == Secp256k1PublicKey.SCHEME:
            return PublicKey(Secp256k1PublicKey(data[1:]))
        else:
            raise TypeError

    def verify(self, msg: bytes, signature: Signature) -> bool:
        return self.value.verify(msg, signature)


class Signature:
    value: Ed25519SuiSignature | Secp256k1SuiSignature

    def __init__(self, signature: Ed25519SuiSignature | Secp256k1SuiSignature) -> None:
        if not isinstance(signature, (Ed25519SuiSignature, Secp256k1SuiSignature)):
            raise TypeError
        self.value = signature

    @staticmethod
    def from_public_signature(pk, sig) -> Signature:
        value = bytearray()
        value.append(pk.scheme())
        value.extend(sig.bytes())
        value.extend(pk.bytes())
        return Signature.from_bytes(bytes(value))

    def bytes(self) -> bytes:
        return self.value.bytes()

    @staticmethod
    def from_base64(b64: str) -> Signature:
        return Signature.from_bytes(b64decode(b64))

    def base64(self) -> str:
        return b64encode(self.bytes()).decode("utf8")

    @staticmethod
    def deserialize(deserializer: Deserializer) -> Signature:
        data = deserializer.bytes()
        return Signature.from_bytes(data)

    @staticmethod
    def from_bytes(data: bytes) -> Signature:
        scheme = data[0]
        if scheme == Ed25519SuiSignature.SCHEME:
            value = Ed25519SuiSignature.from_bytes(data)
        elif scheme == Secp256k1SuiSignature.SCHEME:
            value = Secp256k1SuiSignature.from_bytes(data)
        else:
            raise TypeError

        return Signature(value)

    def serialize(self, serializer: Serializer):
        serializer.bytes(self.bytes())

    def get_verification_inputs(self, author: SuiAddress):
        pk = self.value.public_key
        received = SuiAddress.from_public_key(pk)
        if not received == author:
            raise Exception(
                f"get_verification_inputs Failed. Author is {author}, received is {received}"
            )

        sig = self.value.signature

        return sig, pk

    def verify(self, tx, author: SuiAddress) -> bool:
        sig, pk = self.get_verification_inputs(author)
        msg = tx.bytes()
        print(f"msg: {msg.hex()}")
        return pk.verify(msg, sig)


class Ed25519SuiSignature:
    value: bytes
    LENGTH: int = Ed25519PublicKey.LENGTH + Ed25519Signature.LENGTH + 1
    SCHEME: int = Ed25519PublicKey.SCHEME

    def __init__(self, signature: bytes) -> None:
        if not len(signature) == Ed25519SuiSignature.LENGTH:
            raise Exception(
                f"Expected signature of length {Ed25519SuiSignature.LENGTH}"
            )
        self.value = signature

    @property
    def signature(self) -> Ed25519Signature:
        return Ed25519Signature.from_bytes(self.value[1 : 1 + Ed25519Signature.LENGTH])

    @property
    def public_key(self) -> Ed25519PublicKey:
        return Ed25519PublicKey.from_bytes(self.value[1 + Ed25519Signature.LENGTH :])

    @staticmethod
    def deserialize(deserializer: Deserializer) -> Ed25519SuiSignature:
        signature = deserializer.fixed_bytes(Ed25519SuiSignature.LENGTH)
        return Ed25519SuiSignature(signature)

    @staticmethod
    def from_bytes(data: bytes) -> Ed25519SuiSignature:
        return Ed25519SuiSignature(data)

    def serialize(self, serializer: Serializer):
        serializer.fixed_bytes(self.value)

    def bytes(self) -> bytes:
        return self.value


class Secp256k1SuiSignature:
    value: bytes
    LENGTH: int = Secp256k1PublicKey.LENGTH + Secp256k1Signature.LENGTH + 1
    SCHEME: int = Secp256k1PublicKey.SCHEME

    def __init__(self, signature: bytes) -> None:
        if not len(signature) == Secp256k1SuiSignature.LENGTH:
            raise Exception(
                f"Expected signature of length {Secp256k1SuiSignature.LENGTH}"
            )
        self.value = signature

    @property
    def signature(self) -> Secp256k1Signature:
        return Secp256k1Signature.from_bytes(
            self.value[1 : 1 + Secp256k1Signature.LENGTH]
        )

    @property
    def public_key(self) -> Secp256k1PublicKey:
        return Secp256k1PublicKey.from_bytes(
            self.value[1 + Secp256k1Signature.LENGTH :]
        )

    @staticmethod
    def deserialize(deserializer: Deserializer) -> Secp256k1SuiSignature:
        signature = deserializer.fixed_bytes(Secp256k1SuiSignature.LENGTH)
        return Secp256k1SuiSignature(signature)

    @staticmethod
    def from_bytes(data: bytes) -> Secp256k1SuiSignature:
        return Secp256k1SuiSignature(data)

    def serialize(self, serializer: Serializer):
        serializer.fixed_bytes(self.value)

    def bytes(self) -> bytes:
        return self.value
