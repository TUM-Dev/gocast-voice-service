import logging

import grpc
from google.protobuf import empty_pb2

import subtitles_pb2, subtitles_pb2_grpc
from path import InvalidPathException, file_exists
from taskqueue import TaskQueue
from tasks import GenerationTask


class SubtitleService(subtitles_pb2_grpc.SubtitleGeneratorServicer):
    """grpc service for subtitles"""

    def __init__(self, queue: TaskQueue) -> None:
        self.__queue = queue

    def Generate(self, req: subtitles_pb2.GenerateRequest,
                 context: grpc.ServicerContext) -> empty_pb2.Empty:
        """Handler function for an incoming Generate request.

        Args:
            req: An object holding the grpc message data.
            context: A context object passed to method implementations.
                Visit https://grpc.github.io/grpc/python/grpc.html#service-side-context for more information.

        Returns:
            subtitles_pb2.Empty
        """
        source: str = req.source_file
        language: str = req.language or None
        stream_id: str = req.stream_id

        logging.debug(f'checking if {source} exists')
        try:
            file_exists(source)
        except InvalidPathException as e:
            context.abort(e.grpc_code, e.__str__())

        logging.debug('enqueue generate request')
        self.__queue.put(GenerationTask(source, language, stream_id))

        return empty_pb2.Empty()