from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor


class HelloRequest(_message.Message):
    __slots__ = ("name", "credit_card_number")
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    CREDIT_CARD_NUMBER_FIELD_NUMBER: _ClassVar[int]
    credit_card_number: str
    def __init__(self, name: _Optional[str] = ...,
                 credit_card_number: _Optional[str] = ...) -> None: ...


class HelloResponse(_message.Message):
    __slots__ = ("is_fraud",)
    IS_FRAUD_FIELD_NUMBER: _ClassVar[int]
    is_fraud: str
    def __init__(self, is_fraud: _Optional[str] = ...) -> None: ...
