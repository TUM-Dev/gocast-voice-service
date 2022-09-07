import asyncio
from concurrent import futures
from grpc import aio
from grpc_reflection.v1alpha import reflection
import logging
import os
import vosk
import grpc
import subtitles_pb2
import subtitles_pb2_grpc
import threading

from config import Config


class SubtitleService(subtitles_pb2_grpc.SubtitlesServicer):
    """grpc service for subtitles"""

    def __init__(self, model_paths: [str], base_source: str, base_destination: str) -> None:
        """Initialize service with a given array of paths to models.

        Args:
            model_paths: An array of paths to models for subtitle generation.
        """
        logging.debug(f'loading SubtitleService with models: {model_paths}')
        self.__generators = [vosk.SubtitleGenerator(path) for path in model_paths]
        self.__base_source = base_source
        self.__base_destination = base_destination

    async def Generate(self, req: subtitles_pb2.GenerateRequest,
                       context: grpc.ServicerContext) -> subtitles_pb2.GenerateResponse:
        """ Handler function for an incoming Generate request.

        Iterates the generator list and executes `generate` with the
        requested path as argument.

        Args:
            req (GenerateRequest): An object holding the grpc message data.
            context (grpc.ServicerContext): A context object passed to method implementations.
                Visit https://grpc.github.io/grpc/python/grpc.html#service-side-context for more information.

        Returns:
            Empty object
        """
        source: str = os.path.join(self.__base_source, req.source_file)

        logging.debug(f'checking if {source} exists')
        if not os.path.isfile(source):
            await context.abort(grpc.StatusCode.NOT_FOUND, f'can not find source file: {source}')
            return subtitles_pb2.GenerateResponse()

        if not os.path.isdir(req.destination_folder):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"'destination_folder' is not a folder")

        results = []
        for i, gen in enumerate(self.__generators):
            filename: str = f'{os.path.basename(os.path.splitext(source)[0])}.{gen.get_language()}.srt'
            destination: str = os.path.join(self.__base_destination, req.destination_folder, filename)
            logging.debug(f'{i}: source={source}, destination={destination}')

            results.append(subtitles_pb2.GenerateResponseResults(model=gen.get_model(), destination=destination))

            threading.Thread(target=gen.generate, args=(source, destination)).start()

        return subtitles_pb2.GenerateResponse(source=source, results=results)


async def serve(cfg: Config, debug: bool = False) -> None:
    """Starts the grpc server.

    Args:
        cfg (Config): The configuration of the server.
        debug (bool): Whether the server should be started in debug mode or not.
    """
    server = aio.server(futures.ThreadPoolExecutor(max_workers=10))  # TODO: How to determine how many workers? Guess?
    subtitles_pb2_grpc.add_SubtitlesServicer_to_server(
        servicer=SubtitleService(
            model_paths=cfg['vosk']['models'],
            base_source=cfg['volumes']['base_source'],
            base_destination=cfg['volumes']['base_destination']),
        server=server)

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
    await server.start()
    await server.wait_for_termination()


def main():
    debug = os.environ["DEBUG"] != ""
    logging.basicConfig(level=(logging.INFO, logging.DEBUG)[debug])
    asyncio.run(serve(
        cfg=Config(os.environ["CONFIG_FILE"]),
        debug=debug
    ))


if __name__ == "__main__":
    main()
