from concurrent import futures
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

    def __init__(self, model_paths: [str]):
        """Initialize service with a given array of paths to models.

        Args:
            model_paths: An array of paths to models for subtitle generation.
        """
        logging.debug(f'loading SubtitleService with models: {model_paths}')
        self.__generators = [vosk.SubtitleGenerator(path) for path in model_paths]

    def Generate(self, request: subtitles_pb2.GenerateSubtitlesRequest,
                 context: grpc.ServicerContext) -> subtitles_pb2.GenerateSubtitlesResponse:
        """ Handler function for an incoming Generate request.

        Iterates the generator list and executes `generate` with the
        requested path as argument.

        Args:
            request (GenerateSubtitlesRequest): An object holding the grpc message data.
            context (grpc.ServicerContext): A context object passed to method implementations.
                Visit https://grpc.github.io/grpc/python/grpc.html#service-side-context for more information.

        Returns:
            An GenerateSubtitlesResponse object with response message data.
        """
        results = []
        for i, gen in enumerate(self.__generators):
            logging.debug(f'{i}: generating subtitles for {request.path}')

            subtitles = gen.generate(request.path)
            results.append(subtitles_pb2.GenerateSubtitlesResponseData(
                subtitles=subtitles,
                model=gen.get_model(),
                source=request.path
            ))

        return subtitles_pb2.GenerateSubtitlesResponse(results=results)


def serve(cfg: Config, debug: bool = False) -> None:
    """Starts the grpc server.

    Args:
        cfg (Config): The configuration of the server.
        debug (bool): Whether the server should be started in debug mode or not.
    """
    logging.basicConfig(level=(logging.INFO, logging.DEBUG)[debug])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
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
