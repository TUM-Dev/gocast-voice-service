proto:
	python -m grpc_tools.protoc -I ./protobufs --python_out=./subtitles --grpc_python_out=./subtitles ./protobufs/*.proto \
	&& cp ./subtitles/subtitles_pb2*.py ./mock_receiver/

requirements:
	pip freeze > requirements.txt

lint:
	 flake8 ./voice --exclude=./voice/subtitles_pb2.py,./voice/subtitles_pb2_grpc.py,./voice/audio_pb2.py,./voice/audio_pb2_grpc.py --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics