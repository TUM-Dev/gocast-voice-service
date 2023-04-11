import logging
from google.protobuf import empty_pb2

import audio_pb2_grpc
from path import file_exists, InvalidPathException, dir_exists
from tasks import ExtractAudioTask
from taskqueue import TaskQueue


class AudioService(audio_pb2_grpc.AudioServicer):
    """grpc service for audio related functions"""

    def __init__(self, queue: TaskQueue) -> None:
        self.__queue = queue

    def Extract(self, req, context):
        source: str = req.source_file
        stream_id: str = req.stream_id
        destination: str = req.destination

        logging.debug(f'checking if {source} exists')
        try:
            file_exists(source)
            dir_exists(destination)
        except InvalidPathException as e:
            context.abort(e.grpc_code, e.__str__())

        logging.debug('enqueue extract request')
        self.__queue.put(ExtractAudioTask(source, stream_id, destination))

        return empty_pb2.Empty()
