from google.protobuf import descriptor_pb2

raw = b'\n\x0b\x61\x64hoc.proto\"#\n\x06Person\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0b\n\x03\x61ge\x18\x02 \x01(\x05\x62\x06proto3'


file_descriptor_proto = descriptor_pb2.FileDescriptorProto.FromString(raw)
print(file_descriptor_proto)

proto_string = """
syntax = "proto3";

message Person {
  string name = 1;
  int32 age = 2;
}
"""
