# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: yandex/cloud/api/operation.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import descriptor_pb2 as google_dot_protobuf_dot_descriptor__pb2

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n yandex/cloud/api/operation.proto\x12\x10yandex.cloud.api\x1a google/protobuf/descriptor.proto"/\n\tOperation\x12\x10\n\x08metadata\x18\x01 \x01(\t\x12\x10\n\x08response\x18\x02 \x01(\t:P\n\toperation\x12\x1e.google.protobuf.MethodOptions\x18\xa6\xaa\x05 \x01(\x0b\x32\x1b.yandex.cloud.api.OperationB:Z8github.com/yandex-cloud/go-genproto/yandex/cloud/api;apib\x06proto3'
)


OPERATION_FIELD_NUMBER = 87334
operation = DESCRIPTOR.extensions_by_name["operation"]

_OPERATION = DESCRIPTOR.message_types_by_name["Operation"]
Operation = _reflection.GeneratedProtocolMessageType(
    "Operation",
    (_message.Message,),
    {
        "DESCRIPTOR": _OPERATION,
        "__module__": "yandex.cloud.api.operation_pb2"
        # @@protoc_insertion_point(class_scope:yandex.cloud.api.Operation)
    },
)
_sym_db.RegisterMessage(Operation)

if _descriptor._USE_C_DESCRIPTORS == False:
    google_dot_protobuf_dot_descriptor__pb2.MethodOptions.RegisterExtension(operation)

    DESCRIPTOR._options = None
    DESCRIPTOR._serialized_options = b"Z8github.com/yandex-cloud/go-genproto/yandex/cloud/api;api"
    _OPERATION._serialized_start = 88
    _OPERATION._serialized_end = 135
# @@protoc_insertion_point(module_scope)
