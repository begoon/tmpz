from google.protobuf import text_format, json_format
import adhoc_pb2

message = adhoc_pb2.Person(name="NAME", age=100)
print(message)
print(message.ListFields())
print([[d.name, v] for d, v in message.ListFields()])
print(message.DESCRIPTOR)
print(dir(message))
print(text_format.MessageToString(message))
print(json_format.MessageToDict(message))
