# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: user-code.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='user-code.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0fuser-code.proto\"\"\n\x0eLogProbRequest\x12\x10\n\x08\x62\x36\x34state\x18\x01 \x01(\t\"*\n\x0fLogProbResponse\x12\x17\n\x0flog_prob_result\x18\x01 \x01(\x02\"*\n\x16LogProbGradientRequest\x12\x10\n\x08\x62\x36\x34state\x18\x01 \x01(\t\"5\n\x17LogProbGradientResponse\x12\x1a\n\x12\x62\x36\x34gradient_result\x18\x01 \x01(\t\"\x15\n\x13InitialStateRequest\"0\n\x14InitialStateResponse\x12\x18\n\x10\x62\x36\x34initial_state\x18\x01 \x01(\t2\xbb\x01\n\x08UserCode\x12,\n\x07LogProb\x12\x0f.LogProbRequest\x1a\x10.LogProbResponse\x12\x44\n\x0fLogProbGradient\x12\x17.LogProbGradientRequest\x1a\x18.LogProbGradientResponse\x12;\n\x0cInitialState\x12\x14.InitialStateRequest\x1a\x15.InitialStateResponseb\x06proto3'
)




_LOGPROBREQUEST = _descriptor.Descriptor(
  name='LogProbRequest',
  full_name='LogProbRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='b64state', full_name='LogProbRequest.b64state', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=19,
  serialized_end=53,
)


_LOGPROBRESPONSE = _descriptor.Descriptor(
  name='LogProbResponse',
  full_name='LogProbResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='log_prob_result', full_name='LogProbResponse.log_prob_result', index=0,
      number=1, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=55,
  serialized_end=97,
)


_LOGPROBGRADIENTREQUEST = _descriptor.Descriptor(
  name='LogProbGradientRequest',
  full_name='LogProbGradientRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='b64state', full_name='LogProbGradientRequest.b64state', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=99,
  serialized_end=141,
)


_LOGPROBGRADIENTRESPONSE = _descriptor.Descriptor(
  name='LogProbGradientResponse',
  full_name='LogProbGradientResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='b64gradient_result', full_name='LogProbGradientResponse.b64gradient_result', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=143,
  serialized_end=196,
)


_INITIALSTATEREQUEST = _descriptor.Descriptor(
  name='InitialStateRequest',
  full_name='InitialStateRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=198,
  serialized_end=219,
)


_INITIALSTATERESPONSE = _descriptor.Descriptor(
  name='InitialStateResponse',
  full_name='InitialStateResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='b64initial_state', full_name='InitialStateResponse.b64initial_state', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=221,
  serialized_end=269,
)

DESCRIPTOR.message_types_by_name['LogProbRequest'] = _LOGPROBREQUEST
DESCRIPTOR.message_types_by_name['LogProbResponse'] = _LOGPROBRESPONSE
DESCRIPTOR.message_types_by_name['LogProbGradientRequest'] = _LOGPROBGRADIENTREQUEST
DESCRIPTOR.message_types_by_name['LogProbGradientResponse'] = _LOGPROBGRADIENTRESPONSE
DESCRIPTOR.message_types_by_name['InitialStateRequest'] = _INITIALSTATEREQUEST
DESCRIPTOR.message_types_by_name['InitialStateResponse'] = _INITIALSTATERESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

LogProbRequest = _reflection.GeneratedProtocolMessageType('LogProbRequest', (_message.Message,), {
  'DESCRIPTOR' : _LOGPROBREQUEST,
  '__module__' : 'user_code_pb2'
  # @@protoc_insertion_point(class_scope:LogProbRequest)
  })
_sym_db.RegisterMessage(LogProbRequest)

LogProbResponse = _reflection.GeneratedProtocolMessageType('LogProbResponse', (_message.Message,), {
  'DESCRIPTOR' : _LOGPROBRESPONSE,
  '__module__' : 'user_code_pb2'
  # @@protoc_insertion_point(class_scope:LogProbResponse)
  })
_sym_db.RegisterMessage(LogProbResponse)

LogProbGradientRequest = _reflection.GeneratedProtocolMessageType('LogProbGradientRequest', (_message.Message,), {
  'DESCRIPTOR' : _LOGPROBGRADIENTREQUEST,
  '__module__' : 'user_code_pb2'
  # @@protoc_insertion_point(class_scope:LogProbGradientRequest)
  })
_sym_db.RegisterMessage(LogProbGradientRequest)

LogProbGradientResponse = _reflection.GeneratedProtocolMessageType('LogProbGradientResponse', (_message.Message,), {
  'DESCRIPTOR' : _LOGPROBGRADIENTRESPONSE,
  '__module__' : 'user_code_pb2'
  # @@protoc_insertion_point(class_scope:LogProbGradientResponse)
  })
_sym_db.RegisterMessage(LogProbGradientResponse)

InitialStateRequest = _reflection.GeneratedProtocolMessageType('InitialStateRequest', (_message.Message,), {
  'DESCRIPTOR' : _INITIALSTATEREQUEST,
  '__module__' : 'user_code_pb2'
  # @@protoc_insertion_point(class_scope:InitialStateRequest)
  })
_sym_db.RegisterMessage(InitialStateRequest)

InitialStateResponse = _reflection.GeneratedProtocolMessageType('InitialStateResponse', (_message.Message,), {
  'DESCRIPTOR' : _INITIALSTATERESPONSE,
  '__module__' : 'user_code_pb2'
  # @@protoc_insertion_point(class_scope:InitialStateResponse)
  })
_sym_db.RegisterMessage(InitialStateResponse)



_USERCODE = _descriptor.ServiceDescriptor(
  name='UserCode',
  full_name='UserCode',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=272,
  serialized_end=459,
  methods=[
  _descriptor.MethodDescriptor(
    name='LogProb',
    full_name='UserCode.LogProb',
    index=0,
    containing_service=None,
    input_type=_LOGPROBREQUEST,
    output_type=_LOGPROBRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='LogProbGradient',
    full_name='UserCode.LogProbGradient',
    index=1,
    containing_service=None,
    input_type=_LOGPROBGRADIENTREQUEST,
    output_type=_LOGPROBGRADIENTRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='InitialState',
    full_name='UserCode.InitialState',
    index=2,
    containing_service=None,
    input_type=_INITIALSTATEREQUEST,
    output_type=_INITIALSTATERESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_USERCODE)

DESCRIPTOR.services_by_name['UserCode'] = _USERCODE

# @@protoc_insertion_point(module_scope)
