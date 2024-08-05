all:

GENERATED = .

protobuf:
	python3 \
		-m grpc_tools.protoc \
		--python_out=$(GENERATED) \
		--pyi_out=$(GENERATED) \
		--grpc_python_out=$(GENERATED) \
		-I. \
		route_guide.proto

serve:
	python asyncio_route_guide_server.py

client:
	python asyncio_route_guide_client.py
