.PHONY: gen-proto

gen-proto:
	mkdir -p gen
	protoc --proto_path=protobufs \
		--go_out=gen \
		--go-grpc_out=gen \
		protobufs/subtitles.proto
