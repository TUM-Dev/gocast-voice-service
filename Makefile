proto:
	python -m grpc_tools.protoc -I ./protobufs --python_out=./subtitles --grpc_python_out=./subtitles ./protobufs/subtitles.proto

requirements:
	pip freeze > requirements.txt
