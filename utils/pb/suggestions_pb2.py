# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: suggestions.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'suggestions.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import common_pb2 as common__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11suggestions.proto\x12\x0bsuggestions\x1a\x0c\x63ommon.proto\"5\n\x04\x42ook\x12\x0e\n\x06\x62ookId\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\x12\x0e\n\x06\x61uthor\x18\x03 \x01(\t\"Z\n\x0bSuggestions\x12 \n\x05\x62ooks\x18\x01 \x03(\x0b\x32\x11.suggestions.Book\x12)\n\x0cvector_clock\x18\x02 \x01(\x0b\x32\x13.common.VectorClock2\x87\x01\n\x11SuggestionService\x12\x37\n\nSaySuggest\x12\x0f.common.Request\x1a\x18.suggestions.Suggestions\x12\x39\n\x0einitSuggestion\x12\x18.common.ItemsInitRequest\x1a\r.common.Emptyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'suggestions_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_BOOK']._serialized_start=48
  _globals['_BOOK']._serialized_end=101
  _globals['_SUGGESTIONS']._serialized_start=103
  _globals['_SUGGESTIONS']._serialized_end=193
  _globals['_SUGGESTIONSERVICE']._serialized_start=196
  _globals['_SUGGESTIONSERVICE']._serialized_end=331
# @@protoc_insertion_point(module_scope)
