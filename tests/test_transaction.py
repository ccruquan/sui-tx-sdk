import base64
from yaml import load, Loader

import sui_tx_sdk.transaction as stx
from sui_tx_sdk.sui_address import SuiAddress
from sui_tx_sdk.object import ObjectID, ObjectDigest, ObjectRef
from sui_tx_sdk.bcs import Serializer, Deserializer
from sui_tx_sdk.crypto import Signature


def load_test_data(typ):
    # load kind from sui-tx-test-case.yaml
    with open("sui-tx-test-case.yaml") as f:
        objs = load(f, Loader)
        value = filter(lambda x: typ in x, objs)
        value = [x[typ] for x in value]

        return value


# - Kind:
#     value:
#       TransferObject:
#         recipient: "0xf7c6cd8a54d4b0b2aa75e0c3a5407027d11fd6b8"
#         object_ref:
#           - "0x76a3863d90c99fc89cc82c1072f5887edccf057d"
#           - 1823742269753106181
#           - DPnePK5If6FrZzlp2QOB1KLl2qlNCeZ3DSehQ5MQzQ4=
#     serialization: APfGzYpU1LCyqnXgw6VAcCfRH9a4dqOGPZDJn8icyCwQcvWIftzPBX0Fn3+G7jtPGSAM+d48rkh/oWtnOWnZA4HUouXaqU0J5ncNJ6FDkxDNDg==
#
def get_kind_and_serialization(obj):
    serialization = obj["serialization"]
    obj = get_kind_from_value(obj["value"])
    serialization = base64.b64decode(serialization)
    return obj, serialization


def get_kind_from_value(value):
    value_creator = {
        "TransferObject": create_transfer_object,
        "Publish": create_publish,
        "TransferSui": create_transfer_sui,
        "Pay": create_pay,
        "PaySui": create_pay_sui,
        "PayAllSui": create_pay_all_sui,
        "ChangeEpoch": create_change_epoch,
        # "Call": create_transfer_object,
    }

    for typ, creator in value_creator.items():
        if typ in value:
            return creator(value[typ])

    return None


def create_object_ref(obj):
    id, seq, digest = obj
    id = ObjectID.from_hex(id)
    digest = ObjectDigest.from_base64(digest)
    return ObjectRef(id, seq, digest)


def create_transfer_object(kind):
    recipient = SuiAddress.from_hex(kind["recipient"])
    obj_ref = create_object_ref(kind["object_ref"])
    return stx.TransferObject(recipient, obj_ref)


def create_publish(kind):
    modules = [bytes(x) for x in kind["modules"]]
    return stx.MoveModulePublish(modules)


def create_transfer_sui(kind):
    recipient = SuiAddress.from_hex(kind["recipient"])
    amount = kind.get("amount")
    return stx.TransferSui(recipient, amount)


def create_pay(kind):
    coins = [create_object_ref(x) for x in kind["coins"]]
    recipients = [SuiAddress.from_hex(x) for x in kind["recipients"]]
    amounts = kind["amounts"]

    return stx.Pay(coins, recipients, amounts)


def create_pay_sui(kind):
    coins = [create_object_ref(x) for x in kind["coins"]]
    recipients = [SuiAddress.from_hex(x) for x in kind["recipients"]]
    amounts = kind["amounts"]

    return stx.PaySui(coins, recipients, amounts)


def create_pay_all_sui(kind):
    coins = [create_object_ref(x) for x in kind["coins"]]
    recipient = SuiAddress.from_hex(kind["recipient"])
    return stx.PayAllSui(coins, recipient)


def create_change_epoch(kind):
    epoch = kind["epoch"]
    storage_charge = kind["storage_charge"]
    computation_charge = kind["computation_charge"]
    storage_rebate = kind["storage_rebate"]
    return stx.ChangeEpoch(epoch, storage_charge, computation_charge, storage_rebate)


def serialize_obj(obj):
    ser = Serializer()
    ser.struct(obj)
    return ser.output()


def deserialize_ojb(value, typ):
    deser = Deserializer(value)
    return deser.struct(typ)


kinds = load_test_data("Kind")


class TestKind:
    def test_serialize(self):
        kind_serialization = map(get_kind_and_serialization, kinds)
        objs, serializations = [list(x) for x in zip(*kind_serialization)]

        objs = [stx.SingleTransactionKind(x) for x in objs]
        serialized = map(serialize_obj, objs)
        assert all(a == b for a, b in zip(serialized, serializations))

    def test_deserialize(self):
        kind_serialization = map(get_kind_and_serialization, kinds)
        objs, serializations = [list(x) for x in zip(*kind_serialization)]

        deserialized = (
            deserialize_ojb(x, stx.SingleTransactionKind) for x in serializations
        )
        assert all(x.value == y for x, y in zip(deserialized, objs))


# - TxData:
#     value:
#       kind:
#         Single:
#           TransferObject:
#             recipient: "0xf7c6cd8a54d4b0b2aa75e0c3a5407027d11fd6b8"
#             object_ref:
#               - "0x76a3863d90c99fc89cc82c1072f5887edccf057d"
#               - 1823742269753106181
#               - DPnePK5If6FrZzlp2QOB1KLl2qlNCeZ3DSehQ5MQzQ4=
#       sender: "0x773d761f2c9d18de19bd3b3484cab75abd134ae4"
#       gas_payment:
#         - "0x509c8a306900dc2d6ddfa8e65e93d9adcffa943e"
#         - 2861011113536544275
#         - rXtBmHvhhqAhzw4ZH0HnrNaoOiGlOIwDeWmH4GHUgnE=
#       gas_price: 1
#       gas_budget: 10000
#     serialization: AAD3xs2KVNSwsqp14MOlQHAn0R/WuHajhj2QyZ/InMgsEHL1iH7czwV9BZ9/hu47TxkgDPnePK5If6FrZzlp2QOB1KLl2qlNCeZ3DSehQ5MQzQ53PXYfLJ0Y3hm9OzSEyrdavRNK5FCcijBpANwtbd+o5l6T2a3P+pQ+E17KEHNatCcgrXtBmHvhhqAhzw4ZH0HnrNaoOiGlOIwDeWmH4GHUgnEBAAAAAAAAABAnAAAAAAAA
def get_tx_data_and_serialization(obj):
    serialization = obj["serialization"]
    serialization = base64.b64decode(serialization)

    # TransactionData
    obj = obj["value"]
    sender = SuiAddress.from_hex(obj["sender"])
    payment = create_object_ref(obj["gas_payment"])
    price = obj["gas_price"]
    budget = obj["gas_budget"]

    obj = obj["kind"]
    if "Single" in obj:
        kind = get_kind_from_value(obj["Single"])
        kind = stx.SingleTransactionKind(kind)
    else:
        kind = (get_kind_from_value(x) for x in obj["Batch"])
        kind = [stx.SingleTransactionKind(x) for x in kind]

    kind = stx.TransactionKind(kind)
    tx = stx.TransactionData(kind, sender, payment, price, budget)

    return tx, serialization


tx_datas = load_test_data("TxData")


class TestTxData:
    def test_serialize(self):
        tx_and_serialization = map(get_tx_data_and_serialization, tx_datas)
        txs, serializations = [list(x) for x in zip(*tx_and_serialization)]

        serialized = map(serialize_obj, txs)
        assert all(a == b for a, b in zip(serialized, serializations))

    def test_deserialize(self):
        kind_serialization = map(get_tx_data_and_serialization, tx_datas)
        objs, serializations = [list(x) for x in zip(*kind_serialization)]

        deserialized = map(
            lambda x: deserialize_ojb(x, stx.TransactionData), serializations
        )
        assert all(x == y for x, y in zip(deserialized, objs))


class TestIntent:
    def test_serialize(self):
        intent = stx.Intent(0, 0, 0)
        ser = Serializer()
        ser.struct(intent)
        assert ser.output() == bytes.fromhex("000000")

    def test_deserialize(self):
        deser = Deserializer(bytes.fromhex("000000"))
        intent = deser.struct(stx.Intent)
        assert intent == stx.Intent(0, 0, 0)


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
#               TransferObject:
#                 recipient: "0xf7c6cd8a54d4b0b2aa75e0c3a5407027d11fd6b8"
#                 object_ref:
#                   - "0x76a3863d90c99fc89cc82c1072f5887edccf057d"
#                   - 1823742269753106181
#                   - DPnePK5If6FrZzlp2QOB1KLl2qlNCeZ3DSehQ5MQzQ4=
#           sender: "0x3ee9cbf2224a0c6489156207e2a1bf4fd8c079e9"
#           gas_payment:
#             - "0x3e5ddf88c62d0e06b7019d3e3822c9777a4fbabc"
#             - 8309446808385548704
#             - hwK2r94949cIaxqsPeKSKjFnNkFfdXaZtJCD9bxTNho=
#           gas_price: 1
#           gas_budget: 10000
#       tx_signature: AAr6fTwqiTgQ/JwOAl3rSjgTRgcHrshcHr8UoydBXj3MmK6Vks3gLtDBY2whwMQmog2JvYv25Bl7anLephmdvAoTbNko0neirryuISInMDku3bxjM+3m8Z9KyQAsNqZiVA==
#     serialization: AAAAAAD3xs2KVNSwsqp14MOlQHAn0R/WuHajhj2QyZ/InMgsEHL1iH7czwV9BZ9/hu47TxkgDPnePK5If6FrZzlp2QOB1KLl2qlNCeZ3DSehQ5MQzQ4+6cvyIkoMZIkVYgfiob9P2MB56T5d34jGLQ4GtwGdPjgiyXd6T7q8oPHSzdgVUXMghwK2r94949cIaxqsPeKSKjFnNkFfdXaZtJCD9bxTNhoBAAAAAAAAABAnAAAAAAAAYQAK+n08Kok4EPycDgJd60o4E0YHB67IXB6/FKMnQV49zJiulZLN4C7QwWNsIcDEJqINib2L9uQZe2py3qYZnbwKE2zZKNJ3oq68riEiJzA5Lt28YzPt5vGfSskALDamYlQ=


def get_signed_tx_and_serialization(obj):
    serialization = obj["serialization"]
    serialization = base64.b64decode(serialization)

    # SenderSignedData
    obj = obj["value"]

    sig = Signature.from_base64(obj["tx_signature"])

    # IntentMessage
    obj = obj["intent_message"]

    intent_obj = obj["intent"]
    intent = stx.Intent(
        intent_obj["scope"], intent_obj["version"], intent_obj["app_id"]
    )

    # TransactionData
    obj = obj["value"]

    sender = SuiAddress.from_hex(obj["sender"])
    payment = create_object_ref(obj["gas_payment"])
    price = obj["gas_price"]
    budget = obj["gas_budget"]

    obj = obj["kind"]
    if "Single" in obj:
        kind = get_kind_from_value(obj["Single"])
        kind = stx.SingleTransactionKind(kind)
    else:
        kind = (get_kind_from_value(x) for x in obj["Batch"])
        kind = [stx.SingleTransactionKind(x) for x in kind]

    kind = stx.TransactionKind(kind)
    tx = stx.TransactionData(kind, sender, payment, price, budget)

    intent_message = stx.IntentMessage(intent, tx)

    return stx.SenderSignedData(intent_message, sig), serialization


signed_txs = load_test_data("SignedTx")


class TestSenderSignedData:
    def test_serialize(self):
        signed_tx_and_serialization = map(get_signed_tx_and_serialization, signed_txs)
        txs, serialization = [list(x) for x in zip(*signed_tx_and_serialization)]

        serialized = (serialize_obj(tx) for tx in txs)
        assert all(a == b for a, b in zip(serialized, serialization))

    def test_deserialize(self):
        signed_tx_and_serialization = map(get_signed_tx_and_serialization, signed_txs)
        txs, serialization = [list(x) for x in zip(*signed_tx_and_serialization)]

        objs = (deserialize_ojb(x, stx.SenderSignedData) for x in serialization)
        assert all(a == b for a, b in zip(txs, objs))

    def test_verify(self):
        signed_tx_and_serialization = map(get_signed_tx_and_serialization, signed_txs)
        txs, _ = [list(x) for x in zip(*signed_tx_and_serialization)]
        sigs = (tx.tx_signature for tx in txs)
        datas = (tx.intent_message for tx in txs)
        senders = (tx.intent_message.value.sender for tx in txs)
        assert all(
            sig.verify(data, sender) for sig, data, sender in zip(sigs, datas, senders)
        )
