# Copyright (c) JubiterWallet
# Author: Ruquan
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from nacl.signing import SigningKey, VerifyKey
import typing


class Ed25519KeyPair:
    sk: SigningKey

    def __init__(self, sk: SigningKey) -> None:
        self.sk = sk

    @staticmethod
    def from_private_key(sk: bytes) -> Ed25519KeyPair:
        return Ed25519KeyPair(SigningKey(sk))

    def public_key(self) -> Ed25519PublicKey:
        return Ed25519PublicKey(self.sk.verify_key)

    def private_key_bytes(self):
        return self.sk.encode()

    def sign(self, msg: bytes) -> Ed25519Signature:
        sig = self.sk.sign(msg).signature
        return Ed25519Signature(sig)


class Ed25519PublicKey:
    LENGTH: int = 32
    SCHEME: int = 0
    pk: VerifyKey

    def __init__(self, pk: VerifyKey) -> None:
        self.pk = pk

    @staticmethod
    def scheme() -> int:
        return Ed25519PublicKey.SCHEME

    @staticmethod
    def from_bytes(data: bytes) -> Ed25519PublicKey:
        return Ed25519PublicKey(VerifyKey(data))

    def bytes(self) -> bytes:
        return self.pk.encode()

    def verify(self, msg: bytes, signature: Ed25519Signature) -> bool:
        try:
            self.pk.verify(msg, signature.bytes())
        except Exception:
            return False
        return True

    @staticmethod
    def verify_batch_emtpy_fail(
        msg: bytes,
        pks: typing.List[Ed25519PublicKey],
        sigs: typing.List[Ed25519Signature],
    ) -> bool:
        if len(sigs) == 0:
            raise Exception("Excepted sigs\pkgs")
        if not len(sigs) == len(pks):
            raise Exception(
                "Mismatch between number of signatures and public keys provided"
            )

        return all(pk.verify(msg, sig) for (pk, sig) in zip(pks, sigs))

    @staticmethod
    def verify_batch_emtpy_fail_different_msgs(
        msgs: bytes,
        pks: typing.List[Ed25519PublicKey],
        sigs: typing.List[Ed25519Signature],
    ) -> bool:
        if len(sigs) == 0:
            raise Exception("Excepted msgs\sigs\pkgs")
        if not len(sigs) == len(pks):
            raise Exception(
                "Mismatch between number of messages signatures and public keys provided"
            )

        return all(pk.verify(msg, sig) for (pk, sig, msg) in zip(pks, sigs, msgs))


class Ed25519Signature:
    LENGTH: int = 64
    signature: bytes

    def __init__(self, signature: bytes) -> None:
        if len(signature) != Ed25519Signature.LENGTH:
            raise Exception("Expected signature length 64")
        self.signature = signature

    @staticmethod
    def from_bytes(data: bytes) -> Ed25519PublicKey:
        return Ed25519Signature(data)

    def bytes(self) -> bytes:
        return self.signature
