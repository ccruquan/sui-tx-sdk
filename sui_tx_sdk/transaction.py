# Copyright (c) JubiterWallet
# Author: Ruquan
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
import unittest

from hashlib import sha3_256
from deprecated import deprecated

from .sui_address import SuiAddress
from .bcs import Deserializer, Serializer
from .object import ObjectRef, ObjectDigest
from .type_tag import TypeTag
from .call_arg import CallArg
from .crypto import Signature


class SenderSignedData:
    intent_message: IntentMessage
    tx_signature: Signature

    def __init__(self, data: IntentMessage, signature: Signature) -> None:
        self.intent_message = data
        self.tx_signature = signature

    def __eq__(self, o: SenderSignedData) -> bool:
        return (
            self.intent_message == o.intent_message
            and self.tx_signature == self.tx_signature
        )

    def digest(self) -> ObjectDigest:
        digest = sha3_256(self.intent_message.bytes())
        return ObjectDigest(digest)

    def verify(self) -> bool:
        return self.tx_signature.verify(self.intent_message, self.intent_message.sender)

    @staticmethod
    def deserialize(deserializer: Deserializer) -> SenderSignedData:
        data = deserializer.struct(IntentMessage)
        signature = deserializer.struct(Signature)
        return SenderSignedData(data, signature)

    def serialize(self, serializer: Serializer):
        serializer.struct(self.intent_message)
        serializer.struct(self.tx_signature)


class IntentMessage:
    indent: Intent
    value: TransactionData

    def __init__(self, indent: Intent, msg: TransactionData) -> None:
        super().__init__()
        self.indent = indent
        self.value = msg

    def __eq__(self, o: IntentMessage) -> bool:
        return self.indent == o.indent and self.value == o.value

    @staticmethod
    def from_bytes(bs: bytes) -> IntentMessage:
        deser = Deserializer(bs)
        return IntentMessage.deserialize(deser)

    def bytes(self) -> bytes:
        ser = Serializer()
        self.serialize(ser)
        return ser.output()

    @staticmethod
    def deserialize(deserializer: Deserializer) -> IntentMessage:
        indent = deserializer.struct(Intent)
        msg = deserializer.struct(TransactionData)

        return IntentMessage(indent, msg)

    def serialize(self, serialize: Serializer):
        serialize.struct(self.indent)
        serialize.struct(self.value)


class Intent:
    scope: int
    version: int
    app_id: int

    def __init__(self, scope: int, version: int, app_id: int) -> None:
        self.scope = scope
        self.version = version
        self.app_id = app_id

    def __eq__(self, o: Intent) -> bool:
        return (
            self.scope == o.scope
            and self.version == o.version
            and self.app_id == o.app_id
        )

    @staticmethod
    def from_bytes(bs: bytes) -> Intent:
        deser = Deserializer(bs)
        return Intent.deserialize(deser)

    def bytes(self) -> bytes:
        ser = Serializer()
        self.serialize(ser)
        return ser.output()

    @staticmethod
    def deserialize(deserializer: Deserializer) -> Intent:
        scope = deserializer.u8()
        version = deserializer.u8()
        app_id = deserializer.u8()
        return Intent(scope, version, app_id)

    def serialize(self, serializer: Serializer):
        serializer.u8(self.scope)
        serializer.u8(self.version)
        serializer.u8(self.app_id)


class TransactionData:
    kind: TransactionKind
    sender: SuiAddress
    gas_payment: ObjectRef
    gas_price: int
    gas_budget: int

    def __init__(
        self,
        kind: TransactionKind,
        sender: SuiAddress,
        gas_payment: ObjectRef,
        gas_price: int,
        gas_budget: int,
    ) -> None:
        self.kind = kind
        self.sender = sender
        self.gas_payment = gas_payment
        self.gas_price = gas_price
        self.gas_budget = gas_budget

    def __eq__(self, o: TransactionData) -> bool:
        return (
            self.kind == o.kind
            and self.sender == o.sender
            and self.gas_payment == o.gas_payment
            and self.gas_price == o.gas_price
            and self.gas_budget == o.gas_budget
        )

    @deprecated(
        reason="sui change `sign` style from v0.19.0, see https://github.com/MystenLabs/sui/pull/6445"
    )
    @staticmethod
    def __bcs_signable__():
        return f"{TransactionData.__name__}::"

    @deprecated(
        reason="sui change `sign` style from v0.19.0, see https://github.com/MystenLabs/sui/pull/6445"
    )
    @staticmethod
    def from_signable_bytes(bs: bytes) -> TransactionData:
        name = TransactionData.__bcs_signable__()
        name_len = len(name)
        deserializer = Deserializer(bs[name_len:])
        return TransactionData.deserialize(deserializer)

    @deprecated(
        reason="sui change `sign` style from v0.19.0, see https://github.com/MystenLabs/sui/pull/6445"
    )
    def signable_bytes(self) -> bytes:
        data = bytearray()
        data.extend(self.__bcs_signable__().encode("utf8"))
        serializer = Serializer()
        self.serialize(serializer)
        data.extend(serializer.output())

        return bytes(data)

    @staticmethod
    def from_bytes(bs: bytes) -> TransactionData:
        deser = Deserializer(bs)
        return TransactionData.deserialize(deser)

    def bytes(self) -> bytes:
        ser = Serializer()
        self.serialize(ser)
        return ser.output()

    @staticmethod
    def deserialize(deserializer: Deserializer) -> TransactionData:
        kind = TransactionKind.deserialize(deserializer)
        sender = SuiAddress.deserialize(deserializer)
        gas_payment = ObjectRef.deserialize(deserializer)
        gas_price = deserializer.u64()
        gas_budget = deserializer.u64()

        return TransactionData(kind, sender, gas_payment, gas_price, gas_budget)

    def serialize(self, serializer: Serializer):
        serializer.struct(self.kind)
        serializer.struct(self.sender)
        serializer.struct(self.gas_payment)
        serializer.u64(self.gas_price)
        serializer.u64(self.gas_budget)


class TransactionKind:
    SINGLE: int = 0
    BATCH: int = 1

    variant: int
    value: KIND

    def __init__(self, kind: KIND):
        if isinstance(kind, SingleTransactionKind):
            self.variant = TransactionKind.SINGLE
        elif isinstance(kind, typing.List) and all(
            isinstance(x, SingleTransactionKind) for x in kind
        ):
            self.variant = TransactionKind.BATCH
        else:
            raise TypeError
        self.value = kind

    def __eq__(self, o: TransactionKind) -> bool:
        return self.variant == o.variant and self.value == o.value

    def __str__(self) -> str:
        return self.value.__str__()

    @staticmethod
    def deserialize(deserializer: Deserializer) -> TransactionKind:
        variant = deserializer.uleb128()

        if variant == TransactionKind.SINGLE:
            kind = SingleTransactionKind.deserialize(deserializer)
        elif variant == TransactionKind.BATCH:
            kind = deserializer.sequence(SingleTransactionKind.deserialize)
        else:
            raise TypeError

        return TransactionKind(kind)

    def serialize(self, serializer: Serializer):
        serializer.uleb128(self.variant)
        if isinstance(self.value, SingleTransactionKind):
            self.value.serialize(serializer)
        else:
            serializer.sequence(self.value, Serializer.struct)


class SingleTransactionKind:
    TRANSFER_OBJECT: int = 0
    PUBLISH: int = 1
    CALL: int = 2
    TRANSFER_SUI: int = 3
    PAY: int = 4
    PAY_SUI: int = 5
    PAY_ALL_SUI: int = 6
    CHANGE_EPOCH: int = 7

    variant: int
    value: TX

    def __init__(self, tx: TX) -> None:
        if isinstance(tx, TransferObject):
            self.variant = SingleTransactionKind.TRANSFER_OBJECT
        elif isinstance(tx, MoveModulePublish):
            self.variant = SingleTransactionKind.PUBLISH
        elif isinstance(tx, MoveCall):
            self.variant = SingleTransactionKind.CALL
        elif isinstance(tx, TransferSui):
            self.variant = SingleTransactionKind.TRANSFER_SUI
        elif isinstance(tx, Pay):
            self.variant = SingleTransactionKind.PAY
        elif isinstance(tx, PaySui):
            self.variant = SingleTransactionKind.PAY_SUI
        elif isinstance(tx, PayAllSui):
            self.variant = SingleTransactionKind.PAY_ALL_SUI
        elif isinstance(tx, ChangeEpoch):
            self.variant = SingleTransactionKind.CHANGE_EPOCH
        else:
            raise TypeError
        self.value = tx

    def __eq__(self, o: SingleTransactionKind) -> bool:
        return self.variant == o.variant and self.value == o.value

    def __str__(self) -> str:
        return f"Transaction Kind : {self.value.__kind__()}\n{self.value}\n"

    @staticmethod
    def deserialize(deserializer: Deserializer) -> SingleTransactionKind:
        variant = deserializer.uleb128()
        if variant == SingleTransactionKind.TRANSFER_OBJECT:
            tx = TransferObject.deserialize(deserializer)
        elif variant == SingleTransactionKind.PUBLISH:
            tx = MoveModulePublish.deserialize(deserializer)
        elif variant == SingleTransactionKind.CALL:
            tx = MoveCall.deserialize(deserializer)
        elif variant == SingleTransactionKind.TRANSFER_SUI:
            tx = TransferSui.deserialize(deserializer)
        elif variant == SingleTransactionKind.PAY:
            tx = Pay.deserialize(deserializer)
        elif variant == SingleTransactionKind.PAY_SUI:
            tx = PaySui.deserialize(deserializer)
        elif variant == SingleTransactionKind.PAY_ALL_SUI:
            tx = PayAllSui.deserialize(deserializer)
        elif variant == SingleTransactionKind.CHANGE_EPOCH:
            tx = ChangeEpoch.deserialize(deserializer)
        else:
            raise TypeError
        return SingleTransactionKind(tx)

    def serialize(self, serializer: Serializer):
        serializer.uleb128(self.variant)
        self.value.serialize(serializer)


KIND = SingleTransactionKind | typing.List[SingleTransactionKind]


class TransferObject:
    recipient: SuiAddress
    object_ref: ObjectRef

    def __init__(self, recipient: SuiAddress, object_ref: ObjectRef) -> None:
        self.recipient = recipient
        self.object_ref = object_ref

    def __eq__(self, o: TransferObject) -> bool:
        return self.recipient == o.recipient and self.object_ref == o.object_ref

    def __kind__(self) -> str:
        return "Transfer Object"

    def __str__(self) -> str:
        return f"Recipient : {self.recipient}\n" f"{self.object_ref.__display__()}\n"

    @staticmethod
    def deserialize(deserializer: Deserializer) -> TransferObject:
        recipient = SuiAddress.deserialize(deserializer)
        object_ref = ObjectRef.deserialize(deserializer)
        return TransferObject(recipient, object_ref)

    def serialize(self, serializer: Serializer):
        self.recipient.serialize(serializer)
        self.object_ref.serialize(serializer)


class TransferSui:
    recipient: SuiAddress
    amount: typing.Optional[int]

    def __init__(self, recipient: SuiAddress, amount: typing.Optional[int]):
        self.recipient = recipient
        self.amount = amount

    def __eq__(self, o: TransferSui) -> bool:
        return self.recipient == o.recipient and self.amount == o.amount

    def __kind__(self) -> str:
        return "Transfer SUI"

    def __str__(self) -> str:
        return (
            f"Recipient : {self.recipient}\n"
            f"Amount : {self.amount if self.amount else 'Full Balance'}\n"
        )

    @staticmethod
    def deserialize(deserializer: Deserializer) -> TransferSui:
        recipient = SuiAddress.deserialize(deserializer)
        some = deserializer.bool()
        amount = deserializer.u64() if some else None
        return TransferSui(recipient, amount)

    def serialize(self, serializer: Serializer):
        self.recipient.serialize(serializer)
        serializer.bool(isinstance(self.amount, int))
        if isinstance(self.amount, int):
            serializer.u64(self.amount)


class Pay:
    coins: typing.List[ObjectRef]
    recipients: typing.List[SuiAddress]
    amounts: typing.List[int]

    def __init__(
        self,
        coins: typing.List[ObjectRef],
        recipients: typing.List[SuiAddress],
        amounts: typing.List[int],
    ) -> None:
        if not len(recipients) == len(amounts):
            raise Exception("Expected same count of `recipients` and `amounts`")
        self.coins = coins
        self.recipients = recipients
        self.amounts = amounts

    def __eq__(self, o: Pay) -> bool:
        return (
            self.coins == o.coins
            and self.recipients == o.recipients
            and self.amounts == o.amounts
        )

    def __kind__(self) -> str:
        return "Pay"

    def __str__(self) -> str:
        s = (
            ["Coins :"]
            + [x.__display__() for x in self.coins]
            + ["Recipients :"]
            + [str(x) for x in self.recipients]
            + ["Amounts :"]
            + [str(x) for x in self.amounts]
        )
        return "\n".join(s)

    @staticmethod
    def deserialize(deserializer: Deserializer) -> Pay:
        coins = deserializer.sequence(ObjectRef.deserialize)
        recipients = deserializer.sequence(SuiAddress.deserialize)
        amounts = deserializer.sequence(Deserializer.u64)
        return Pay(coins, recipients, amounts)

    def serialize(self, serializer: Serializer):
        serializer.sequence(self.coins, Serializer.struct)
        serializer.sequence(self.recipients, Serializer.struct)
        serializer.sequence(self.amounts, Serializer.u64)


class PaySui:
    coins: typing.List[ObjectRef]
    recipients: typing.List[SuiAddress]
    amounts: typing.List[int]

    def __init__(
        self,
        coins: typing.List[ObjectRef],
        recipients: typing.List[SuiAddress],
        amounts: typing.List[int],
    ) -> None:
        if not len(recipients) == len(amounts):
            raise Exception("Expected same count of `recipients` and `amounts`")
        self.coins = coins
        self.recipients = recipients
        self.amounts = amounts

    def __eq__(self, o: PaySui) -> bool:
        return (
            self.coins == o.coins
            and self.recipients == o.recipients
            and self.amounts == o.amounts
        )

    def __kind__(self) -> str:
        return "Pay SUI"

    def __str__(self) -> str:
        s = (
            ["Coins :"]
            + [x.__display__() for x in self.coins]
            + ["Recipients :"]
            + [str(x) for x in self.recipients]
            + ["Amounts :"]
            + [str(x) for x in self.amounts]
        )
        return "\n".join(s)

    @staticmethod
    def deserialize(deserializer: Deserializer) -> PaySui:
        coins = deserializer.sequence(ObjectRef.deserialize)
        recipients = deserializer.sequence(SuiAddress.deserialize)
        amounts = deserializer.sequence(Deserializer.u64)
        return PaySui(coins, recipients, amounts)

    def serialize(self, serializer: Serializer):
        serializer.sequence(self.coins, Serializer.struct)
        serializer.sequence(self.recipients, Serializer.struct)
        serializer.sequence(self.amounts, Serializer.u64)


class PayAllSui:
    coins: typing.List[ObjectRef]
    recipient: SuiAddress

    def __init__(
        self,
        coins: typing.List[ObjectRef],
        recipient: SuiAddress,
    ) -> None:
        self.coins = coins
        self.recipient = recipient

    def __eq__(self, o: PayAllSui) -> bool:
        return self.coins == o.coins and self.recipient == o.recipient

    def __kind__(self) -> str:
        return "Pay all SUI"

    def __str__(self) -> str:
        s = (
            ["Coins :"]
            + [x.__display__() for x in self.coins]
            + ["Recipient :"]
            + str(self.recipient)
        )
        return "\n".join(s)

    @staticmethod
    def deserialize(deserializer: Deserializer) -> PayAllSui:
        coins = deserializer.sequence(ObjectRef.deserialize)
        recipient = SuiAddress.deserialize(deserializer)
        return PayAllSui(coins, recipient)

    def serialize(self, serializer: Serializer):
        serializer.sequence(self.coins, Serializer.struct)
        self.recipient.serialize(serializer)


class ChangeEpoch:
    epoch: int
    storage_charge: int
    computation_charge: int
    storage_rebate: int

    def __init__(
        self,
        epoch: int,
        storage_charge: int,
        computation_charge: int,
        storage_rebate: int,
    ):
        self.epoch = epoch
        self.storage_charge = storage_charge
        self.computation_charge = computation_charge
        self.storage_rebate = storage_rebate

    def __eq__(self, o: ChangeEpoch) -> bool:
        return (
            self.epoch == o.epoch
            and self.storage_charge == o.storage_charge
            and self.computation_charge == o.computation_charge
            and self.storage_rebate == o.storage_rebate
        )

    def __kind__(self) -> str:
        return "Epoch Change"

    def __str__(self) -> str:
        return (
            f"New epoch ID : {self.epoch}\n"
            f"Storage gas reward : {self.storage_charge}\n"
            f"Computation gas reward : {self.computation_charge}\n"
            f"Storage rebate : {self.storage_rebate}\n"
        )

    @staticmethod
    def deserialize(deserializer: Deserializer) -> ChangeEpoch:
        epoch = deserializer.u64()
        storage_charge = deserializer.u64()
        computation_charge = deserializer.u64()
        storage_rebate = deserializer.u64()
        return ChangeEpoch(epoch, storage_charge, computation_charge, storage_rebate)

    def serialize(self, serializer: Serializer):
        serializer.u64(self.epoch)
        serializer.u64(self.storage_charge)
        serializer.u64(self.computation_charge)
        serializer.u64(self.storage_rebate)


class MoveModulePublish:
    modules: typing.List[bytes]

    def __init__(self, modules: typing.List[bytes]):
        self.modules = modules

    def __eq__(self, o: MoveModulePublish) -> bool:
        return self.modules == o.modules

    def __kind__(self) -> str:
        return "Publish"

    def __str__(self) -> str:
        return ""

    @staticmethod
    def deserialize(deserializer: Deserializer) -> MoveModulePublish:
        modules = deserializer.sequence(Deserializer.bytes)
        return MoveModulePublish(modules)

    def serialize(self, serializer: Serializer):
        serializer.sequence(self.modules, Serializer.bytes)


class MoveCall:
    package: ObjectRef
    module: str
    function: str
    type_args: typing.List[TypeTag]
    args: typing.List[CallArg]

    def __init__(
        self,
        package: ObjectRef,
        module: str,
        function: str,
        type_args: typing.List[TypeTag],
        args: typing.List[CallArg],
    ):
        self.package = package
        self.module = module
        self.function = function
        self.type_args = type_args
        self.args = args

    def __eq__(self, o: MoveCall) -> bool:
        return (
            self.package == o.package
            and self.module == o.module
            and self.function == o.function
            and self.type_args == o.type_args
            and self.args == o.args
        )

    def __kind__(self) -> str:
        return "Call"

    def __str__(self) -> str:
        return (
            f"Package ID : {self.package.object_id}\n"
            f"Module : {self.module}\n"
            f"Function : {self.function}\n"
            f"Arguments : {self.args.__repr__()}\n"
            f"Type Arguments : {self.type_args.__repr__()}\n"
        )

    @staticmethod
    def deserialize(deserializer: Deserializer) -> MoveCall:
        package = ObjectRef.deserialize(deserializer)
        module = deserializer.str()
        function = deserializer.str()
        type_args = deserializer.sequence(TypeTag.deserialize)
        args = deserializer.sequence(CallArg.deserialize)
        return MoveCall(package, module, function, type_args, args)

    def serialize(self, serializer: Serializer):
        serializer.struct(self.package)
        serializer.str(self.module)
        serializer.str(self.function)
        serializer.sequence(self.type_args, Serializer.struct)
        serializer.sequence(self.args, Serializer.struct)


TX = (
    TransferObject
    | MoveModulePublish
    | MoveCall
    | TransferSui
    | Pay
    | PaySui
    | PayAllSui
    | ChangeEpoch
)
