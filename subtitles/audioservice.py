import logging
from google.protobuf import empty_pb2

import audio_pb2_grpc
from path import is_valid_path, InvalidPathException
from tasks import ExtractAudioTask
from taskqueue import TaskQueue


class AudioService(audio_pb2_grpc.AudioServicer):
    """grpc service for audio related functions"""

    def __init__(self, queue: TaskQueue) -> None:
        self.__queue = queue

    def Extract(self, req, context):
        source: str = req.source_file
        stream_id: str = req.stream_id

        logging.debug(f'checking if {source} exists')
        try:
            is_valid_path(source)
        except InvalidPathException as e:
            context.abort(e.grpc_code, e.__str__())

        logging.debug('enqueue extract request')
        self.__queue.put(ExtractAudioTask(source, stream_id))

        return empty_pb2.Empty()
