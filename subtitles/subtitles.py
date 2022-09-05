import sys
import threading
import time
from concurrent import futures

import google
from grpc_reflection.v1alpha import reflection
import logging
import os
import vosk
import grpc
import subtitles_pb2
import subtitles_pb2_grpc

from config import Config


class SubtitleService(subtitles_pb2_grpc.SubtitlesServicer):
    """grpc service for subtitles"""

    def __init__(self, model_paths: [str]) -> None:
        """Initialize service with a given array of paths to models.

        Args:
            model_paths: An array of paths to models for subtitle generation.
        """
        logging.debug(f'loading SubtitleService with models: {model_paths}')
        self.__generators = [vosk.SubtitleGenerator(path) for path in model_paths]

    def Generate(self, req: subtitles_pb2.GenerateRequest,
                 context: grpc.ServicerContext) -> subtitles_pb2.Empty:
        """ Handler function for an incoming Generate request.

        Iterates the generator list and executes `generate` with the
        requested path as argument.

        Args:
            req (GenerateRequest): An object holding the grpc message data.
            context (grpc.ServicerContext): A context object passed to method implementations.
                Visit https://grpc.github.io/grpc/python/grpc.html#service-side-context for more information.

        Returns:
            Empty Object
        """
        for i, gen in enumerate(self.__generators):
            logging.debug(f'{i}: generating subtitles for {req.source_file}')

            logging.debug(f'{i}: checking if {req.source_file} exists')
            if not os.path.isfile(req.source_file):
                context.abort(grpc.StatusCode.NOT_FOUND, f'source file ({req.source_file}) does not exists')
                return

            try:
                logging.debug(f'{i}: calling generate({req.source_file})')
                gen.generate(req.source_file, req.destin_file)
            except Exception as err:
                context.abort(grpc.StatusCode.UNKNOWN, err)
                return

        return subtitles_pb2.Empty()


def serve(cfg: Config, debug: bool = False) -> None:
    """Starts the grpc server.

    Args:
        cfg (Config): The configuration of the server.
        debug (bool): Whether the server should be started in debug mode or not.
    """
    logging.basicConfig(level=(logging.INFO, logging.DEBUG)[debug])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))  # TODO: How to determine how many workers? Guess?
    service = SubtitleService(
        model_paths=cfg['vosk']['models']
    )
    subtitles_pb2_grpc.add_SubtitlesServicer_to_server(service, server)

    if debug:
        logging.debug('starting server with reflection activated.')
        service_names = (
            subtitles_pb2.DESCRIPTOR.services_by_name['Subtitles'].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(service_names, server)

    port = cfg['api']['port']
    logging.info(f'listening at :{port}')
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve(
        cfg=Config(os.environ["CONFIG_FILE"]),
        debug=os.environ["DEBUG"] != ""
    )
