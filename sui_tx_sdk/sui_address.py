# Copyright (c) JubiterWallet
# Author: Ruquan
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
import hashlib

from .bcs import Deserializer, Serializer
from .account_address import AccountAddress


class SuiAddress:
    address: bytes
    LENGTH: int = 20

    def __init__(self, address: bytes) -> None:
        if len(address) != SuiAddress.LENGTH:
            raise Exception("Expected address of length 20")
        self.address = address

    def __eq__(self, o: SuiAddress) -> bool:
        return self.address == o.address

    def __str__(self) -> str:
        return self.hex()

    def hex(self) -> str:
        return f"0x{self.address.hex()}"

    @staticmethod
    def from_account_address(address: AccountAddress) -> SuiAddress:
        return SuiAddress(address.address)

    @staticmethod
    def from_public_key(pk) -> SuiAddress:
        """generate address from `Public key`

        Class which have `scheme` `bytes` method can use as Public key.

        Class: `PublicKey` `SuiPublicKey` `Ed25519SuiPublicKey` `Ed25519PublicKey`
        `Secp256k1SuiPublicKey` `Secp256k1Public`
        """
        sha3_256 = hashlib.sha3_256()
        sha3_256.update(bytes([pk.scheme()]))
        sha3_256.update(pk.bytes())
        digest = sha3_256.digest()
        return SuiAddress(digest[: SuiAddress.LENGTH])

    @staticmethod
    def from_hex(address: str) -> SuiAddress:
        if address.startswith("0x") or address.startswith("0X"):
            address = address[2:]

        address = "0" * (SuiAddress.LENGTH * 2 - len(address)) + address
        return SuiAddress(bytes.fromhex(address))

    @staticmethod
    def deserialize(deserializer: Deserializer) -> SuiAddress:
        return SuiAddress(deserializer.fixed_bytes(SuiAddress.LENGTH))

    def serialize(self, serializer: Serializer):
        serializer.fixed_bytes(self.address)
