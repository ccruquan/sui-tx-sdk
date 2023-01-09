# Copyright (c) JubiterWallet
# Author: Ruquan
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from hashlib import sha256
import secp256k1
import typing


class Secp256k1KeyPair:
    sk: secp256k1.PrivateKey

    def __init__(self, sk: secp256k1.PrivateKey) -> None:
        self.sk = sk

    @staticmethod
    def from_private_key(sk: bytes) -> Secp256k1KeyPair:
        return Secp256k1KeyPair(secp256k1.PrivateKey(sk))

    def public_key(self) -> Secp256k1PublicKey:
        return Secp256k1PublicKey(self.sk.pubkey)

    def private_key_bytes(self):
        hex = self.sk.serialize()
        return bytes.fromhex(hex)

    def sign(self, msg: bytes) -> Secp256k1Signature:
        sig = self.sk.ecdsa_sign_recoverable(msg)
        rs, v = self.sk.ecdsa_recoverable_serialize(sig)
        data = bytearray()
        data.extend(rs)
        data.append(v)
        return Secp256k1Signature(bytes(data))


class Secp256k1PublicKey:
    LENGTH: int = 33
    SCHEME: int = 1
    pk: secp256k1.PublicKey

    def __init__(self, pk: secp256k1.PublicKey) -> None:
        self.pk = pk

    @staticmethod
    def scheme() -> int:
        return Secp256k1PublicKey.SCHEME

    @staticmethod
    def from_bytes(data: bytes) -> Secp256k1PublicKey:
        if len(data) != Secp256k1PublicKey.LENGTH:
            raise Exception("Expected compressed key of length 33")
        return Secp256k1PublicKey(secp256k1.PublicKey(data, True))

    def bytes(self) -> bytes:
        return self.pk.serialize()

    def verify(self, msg: bytes, signature: Secp256k1Signature):
        try:
            ecdsa = secp256k1.ECDSA()
            signature = signature.bytes()
            sig = ecdsa.ecdsa_recoverable_deserialize(signature[:64], signature[64])
            recovered = ecdsa.ecdsa_recover(msg, sig)
            recovered = secp256k1.PublicKey(recovered)
            return self.pk.serialize() == recovered.serialize()
        except Exception:
            return False
        return True

    @staticmethod
    def verify_batch_emtpy_fail(
        msg: bytes,
        pks: typing.List[Secp256k1PublicKey],
        sigs: typing.List[Secp256k1Signature],
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
        pks: typing.List[Secp256k1PublicKey],
        sigs: typing.List[Secp256k1Signature],
    ) -> bool:
        if len(sigs) == 0:
            raise Exception("Excepted msgs\sigs\pkgs")
        if not len(sigs) == len(pks):
            raise Exception(
                "Mismatch between number of messages signatures and public keys provided"
            )

        return all(pk.verify(msg, sig) for (pk, sig, msg) in zip(pks, sigs, msgs))


class Secp256k1Signature:
    LENGTH: int = 65
    signature: bytes

    def __init__(self, signature: bytes) -> None:
        if len(signature) != Secp256k1Signature.LENGTH:
            raise Exception("Expected signature length 64")
        self.signature = signature

    @staticmethod
    def from_bytes(data: bytes) -> Secp256k1Signature:
        return Secp256k1Signature(data)

    def bytes(self) -> bytes:
        return self.signature
