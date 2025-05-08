import common_pb2 as _common_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class InitRequest(_message.Message):
    __slots__ = ("order_id", "transaction_request")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_REQUEST_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    transaction_request: _common_pb2.AllInfoRequest
    def __init__(self, order_id: _Optional[str] = ..., transaction_request: _Optional[_Union[_common_pb2.AllInfoRequest, _Mapping]] = ...) -> None: ...
