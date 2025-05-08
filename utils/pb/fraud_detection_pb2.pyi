import common_pb2 as _common_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class OrderResponse(_message.Message):
    __slots__ = ("is_fraud", "message")
    IS_FRAUD_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    is_fraud: bool
    message: str
    def __init__(self, is_fraud: bool = ..., message: _Optional[str] = ...) -> None: ...
