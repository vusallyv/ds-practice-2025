from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PrepareRequest(_message.Message):
    __slots__ = ("order_id", "amount", "title")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    amount: int
    title: str
    def __init__(self, order_id: _Optional[str] = ..., amount: _Optional[int] = ..., title: _Optional[str] = ...) -> None: ...

class PrepareResponse(_message.Message):
    __slots__ = ("ready",)
    READY_FIELD_NUMBER: _ClassVar[int]
    ready: bool
    def __init__(self, ready: bool = ...) -> None: ...

class CommitRequest(_message.Message):
    __slots__ = ("order_id", "title")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    title: str
    def __init__(self, order_id: _Optional[str] = ..., title: _Optional[str] = ...) -> None: ...

class CommitResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class AbortRequest(_message.Message):
    __slots__ = ("order_id",)
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    def __init__(self, order_id: _Optional[str] = ...) -> None: ...

class AbortResponse(_message.Message):
    __slots__ = ("aborted",)
    ABORTED_FIELD_NUMBER: _ClassVar[int]
    aborted: bool
    def __init__(self, aborted: bool = ...) -> None: ...

class VectorClock(_message.Message):
    __slots__ = ("clocks",)
    CLOCKS_FIELD_NUMBER: _ClassVar[int]
    clocks: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, clocks: _Optional[_Iterable[int]] = ...) -> None: ...

class Request(_message.Message):
    __slots__ = ("order_id", "vector_clock")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    VECTOR_CLOCK_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    vector_clock: VectorClock
    def __init__(self, order_id: _Optional[str] = ..., vector_clock: _Optional[_Union[VectorClock, _Mapping]] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ("fail", "message", "vector_clock")
    FAIL_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    VECTOR_CLOCK_FIELD_NUMBER: _ClassVar[int]
    fail: bool
    message: str
    vector_clock: VectorClock
    def __init__(self, fail: bool = ..., message: _Optional[str] = ..., vector_clock: _Optional[_Union[VectorClock, _Mapping]] = ...) -> None: ...

class Item(_message.Message):
    __slots__ = ("name", "quantity")
    NAME_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    name: str
    quantity: int
    def __init__(self, name: _Optional[str] = ..., quantity: _Optional[int] = ...) -> None: ...

class InitAllInfoRequest(_message.Message):
    __slots__ = ("order_id", "request")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    request: AllInfoRequest
    def __init__(self, order_id: _Optional[str] = ..., request: _Optional[_Union[AllInfoRequest, _Mapping]] = ...) -> None: ...

class AllInfoRequest(_message.Message):
    __slots__ = ("name", "contact", "credit_card_number", "expiration_date", "cvv", "billing_address", "quantity", "items")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONTACT_FIELD_NUMBER: _ClassVar[int]
    CREDIT_CARD_NUMBER_FIELD_NUMBER: _ClassVar[int]
    EXPIRATION_DATE_FIELD_NUMBER: _ClassVar[int]
    CVV_FIELD_NUMBER: _ClassVar[int]
    BILLING_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    name: str
    contact: str
    credit_card_number: str
    expiration_date: str
    cvv: int
    billing_address: str
    quantity: int
    items: _containers.RepeatedCompositeFieldContainer[Item]
    def __init__(self, name: _Optional[str] = ..., contact: _Optional[str] = ..., credit_card_number: _Optional[str] = ..., expiration_date: _Optional[str] = ..., cvv: _Optional[int] = ..., billing_address: _Optional[str] = ..., quantity: _Optional[int] = ..., items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ...) -> None: ...

class ItemsInitRequest(_message.Message):
    __slots__ = ("order_id", "items")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    items: _containers.RepeatedCompositeFieldContainer[Item]
    def __init__(self, order_id: _Optional[str] = ..., items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
