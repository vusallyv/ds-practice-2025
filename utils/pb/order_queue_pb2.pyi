import common_pb2 as _common_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class LeaderRequest(_message.Message):
    __slots__ = ("sender_id",)
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    sender_id: str
    def __init__(self, sender_id: _Optional[str] = ...) -> None: ...
