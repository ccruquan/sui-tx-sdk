import base64
from sui_tx_sdk.object import ObjectID, ObjectDigest, ObjectRef
from sui_tx_sdk.bcs import Deserializer, Serializer

object_id = "0x76a3863d90c99fc89cc82c1072f5887edccf057d"
object_seq = 1823742269753106181
object_digest = "DPnePK5If6FrZzlp2QOB1KLl2qlNCeZ3DSehQ5MQzQ4="


def test_object_id():
    id_from_hex = ObjectID.from_hex(object_id)
    value = bytes.fromhex(object_id[2:])
    deser = Deserializer(value)
    id_from_deser = deser.struct(ObjectID)
    assert id_from_deser == id_from_hex


def test_object_id_serialization():
    id_from_hex = ObjectID.from_hex(object_id)
    ser = Serializer()
    ser.struct(id_from_hex)
    assert ser.output() == bytes.fromhex("76a3863d90c99fc89cc82c1072f5887edccf057d")


def test_object_digest():
    digest_from_base64 = ObjectDigest.from_base64(object_digest)
    value = base64.b64decode(object_digest)
    digest = ObjectDigest(value)
    assert digest == digest_from_base64


def test_object_digest_serialization():
    digest_from_base64 = ObjectDigest.from_base64(object_digest)
    ser = Serializer()
    ser.struct(digest_from_base64)

    assert ser.output() == bytes.fromhex(
        "200cf9de3cae487fa16b673969d90381d4a2e5daa94d09e6770d27a1439310cd0e"
    )


def test_objectref_serialization():
    id = ObjectID.from_hex(object_id)
    digest = ObjectDigest.from_base64(object_digest)

    ref = ObjectRef(id, object_seq, digest)
    ser = Serializer()
    ser.struct(ref)

    serialization = (
        "76a3863d90c99fc89cc82c1072f5887edccf057d"
        "059f7f86ee3b4f19"
        "200cf9de3cae487fa16b673969d90381d4a2e5daa94d09e6770d27a1439310cd0e"
    )
    assert ser.output() == bytes.fromhex(serialization)
