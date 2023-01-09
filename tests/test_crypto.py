import base64
from yaml import load, Loader
import random
from sui_tx_sdk.crypto import (
    SuiKeyPair,
    Signature,
    Ed25519SuiSignature,
    Secp256k1SuiSignature,
)
from sui_tx_sdk.transaction import (
    TransactionData,
    TransactionKind,
    SingleTransactionKind,
    ChangeEpoch,
    IntentMessage,
    Intent,
)
from sui_tx_sdk.sui_address import SuiAddress
from sui_tx_sdk.object import ObjectRef, ObjectID, ObjectDigest

from sui_tx_sdk.bcs import Deserializer, Serializer

# load key pairs from sui-tx-test-case.yaml
with open("sui-tx-test-case.yaml") as f:
    objs = load(f, Loader)
    key_pairs = filter(lambda x: "KeyPair" in x, objs)
    key_pairs = [x["KeyPair"] for x in key_pairs]


class TestSuiKeyPair:
    def test_base64(self):
        for key_pair in key_pairs:
            b64 = key_pair["serialization"]
            kp = SuiKeyPair.from_base64(b64)
            assert kp.base64() == b64

    def test_sign(self):
        data = random.randbytes(256)
        for key_pair in key_pairs:
            b64 = key_pair["value"]
            kp = SuiKeyPair.from_base64(b64)
            sig = kp.sign(data)
            assert kp.public_key().verify(data, sig.value.signature)


class TestSignature:
    def test_base64(self):
        b64 = "AbcPbZFJ0Lo4KgQJiLg+XNUsDq2WR9Xk71aa41lMr+w5JU7ify401eKb9B+0jE0xstieclx/C4s9UhZKQfRLJUwBAhprpMRv9DO2b3mZLGTfT0nNcLBPOHBKMfZsdbN4BvtQ"
        data = base64.b64decode(b64)
        signature = Signature.from_bytes(data)
        assert b64 == signature.base64()

    def test_verify(self):
        # - SignedTx:
        #     value:
        #       intent_message:
        #         intent:
        #           scope: 0
        #           version: 0
        #           app_id: 0
        #         value:
        #           kind:
        #             Single:
        #               ChangeEpoch:
        #                 epoch: 14243162577038171666
        #                 storage_charge: 5840114913121866738
        #                 computation_charge: 9397292174379519512
        #                 storage_rebate: 4399458899819481778
        #           sender: "0x3652dfdd13b53ee0e09bc2f2e302bc33c2d8133b"
        #           gas_payment:
        #             - "0xeac7c32881d1d9974f2c92455879cea9da78c3a1"
        #             - 10479749035751141357
        #             - nOteHzhuytKp0Bb5QzFJDftpmXYpoR6myaiRwAr55dY=
        #           gas_price: 1
        #           gas_budget: 10000
        #       tx_signature: AWHLA5TQjKc2rkXk7v6hhHL7KEjcrsHCUg7VGYOnJwwbSUl/M/u7VAxxIp5GSyJ9Eu3GoQ06c/0Mf4wYRiLcF6QBAhprpMRv9DO2b3mZLGTfT0nNcLBPOHBKMfZsdbN4BvtQ
        #     serialization: AAAAAAcSXn965uCpxfITFzySQQxRGA5zkHHjaYKyyqtfjwQOPTZS390TtT7g4JvC8uMCvDPC2BM76sfDKIHR2ZdPLJJFWHnOqdp4w6HtbzBTOYxvkSCc614fOG7K0qnQFvlDMUkN+2mZdimhHqbJqJHACvnl1gEAAAAAAAAAECcAAAAAAABjAWHLA5TQjKc2rkXk7v6hhHL7KEjcrsHCUg7VGYOnJwwbSUl/M/u7VAxxIp5GSyJ9Eu3GoQ06c/0Mf4wYRiLcF6QBAhprpMRv9DO2b3mZLGTfT0nNcLBPOHBKMfZsdbN4BvtQ

        payment = ObjectRef(
            ObjectID.from_hex("0xeac7c32881d1d9974f2c92455879cea9da78c3a1"),
            10479749035751141357,
            ObjectDigest.from_base64("nOteHzhuytKp0Bb5QzFJDftpmXYpoR6myaiRwAr55dY="),
        )
        tx = TransactionData(
            TransactionKind(
                SingleTransactionKind(
                    ChangeEpoch(
                        14243162577038171666,
                        5840114913121866738,
                        9397292174379519512,
                        4399458899819481778,
                    )
                )
            ),
            SuiAddress.from_hex("0x3652dfdd13b53ee0e09bc2f2e302bc33c2d8133b"),
            payment,
            1,
            10000,
        )

        intent_tx = IntentMessage(Intent(0, 0, 0), tx)
        b64 = base64.b64decode(
            "AWHLA5TQjKc2rkXk7v6hhHL7KEjcrsHCUg7VGYOnJwwbSUl/M/u7VAxxIp5GSyJ9Eu3GoQ06c/0Mf4wYRiLcF6QBAhprpMRv9DO2b3mZLGTfT0nNcLBPOHBKMfZsdbN4BvtQ"
        )
        signatue = Signature.from_bytes(b64)
        assert signatue.verify(intent_tx, tx.sender)


class TestEd25519SuiSignature:
    value = "AAr6fTwqiTgQ/JwOAl3rSjgTRgcHrshcHr8UoydBXj3MmK6Vks3gLtDBY2whwMQmog2JvYv25Bl7anLephmdvAoTbNko0neirryuISInMDku3bxjM+3m8Z9KyQAsNqZiVA=="

    def test_from_bytes(self):
        value = base64.b64decode(self.value)
        sig = Ed25519SuiSignature.from_bytes(value)

    def test_deserialize(self):
        value = base64.b64decode(self.value)
        deser = Deserializer(value)
        sig = deser.struct(Ed25519SuiSignature)

        ser = Serializer()
        ser.struct(sig)
        assert ser.output() == value


class TestSecp256k1SuiSignature:
    value = "AWHLA5TQjKc2rkXk7v6hhHL7KEjcrsHCUg7VGYOnJwwbSUl/M/u7VAxxIp5GSyJ9Eu3GoQ06c/0Mf4wYRiLcF6QBAhprpMRv9DO2b3mZLGTfT0nNcLBPOHBKMfZsdbN4BvtQ"

    def test_from_bytes(self):
        value = base64.b64decode(self.value)
        sig = Secp256k1SuiSignature.from_bytes(value)

    def test_deserialize(self):
        value = base64.b64decode(self.value)
        deser = Deserializer(value)
        sig = deser.struct(Secp256k1SuiSignature)

        ser = Serializer()
        ser.struct(sig)
        assert ser.output() == value
