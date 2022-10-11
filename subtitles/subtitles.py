import asyncio
import sys
import threading
from concurrent import futures
from grpc import aio
from grpc_reflection.v1alpha import reflection
from vosk_generator import SubtitleGenerator
import logging
import os
import grpc
import subtitles_pb2
import subtitles_pb2_grpc
from properties import YAMLPropertiesFile, EnvProperties, PropertyError


class SubtitleServerService(subtitles_pb2_grpc.SubtitleGeneratorServicer):
    """grpc service for subtitles"""

    def __init__(self, models: [object], receiver: str) -> None:
        """Initialize service with a given array of paths to models.

        Args:
            models: An array of model objects.
            receiver: The address of the receiver service.
        """
        logging.debug(f'loading SubtitleService with models: {models}')
        self.__generators = [SubtitleGenerator(model['path'], model['lang']) for model in models]
        self.__receiver = receiver

    async def Generate(self, req: subtitles_pb2.GenerateRequest,
                       context: grpc.ServicerContext) -> subtitles_pb2.Empty:
        """ Handler function for an incoming Generate request.

        Iterates the generator list and executes `generate` with the
        requested path as argument.

        Args:
            req (GenerateRequest): An object holding the grpc message data.
            context (grpc.ServicerContext): A context object passed to method implementations.
                Visit https://grpc.github.io/grpc/python/grpc.html#service-side-context for more information.

        Returns:
            subtitles_pb2.Empty
        """
        source: str = req.source_file

        logging.debug(f'checking if {source} exists')
        if not os.path.isfile(source):
            await context.abort(grpc.StatusCode.NOT_FOUND, f'can not find source file: {source}')
            return subtitles_pb2.Empty()

        for i, gen in enumerate(self.__generators):
            threading.Thread(target=self.__generate, args=(gen, source, req.stream_id)).start()

        return subtitles_pb2.Empty()

    def __generate(self, gen: SubtitleGenerator, source: str, stream_id: str) -> None:
        subtitles = gen.generate(source)
        logging.debug(f'stream_id={stream_id}; subtitles={subtitles[:32]}')

        logging.info(f'trying to connect to receiver @ {self.__receiver}')
        with grpc.insecure_channel(self.__receiver) as channel:
            stub = subtitles_pb2_grpc.SubtitleReceiverStub(channel)
            stub.Receive(
                subtitles_pb2.ReceiveRequest(stream_id=stream_id, subtitles=subtitles, language=gen.get_language()))


async def serve(properties: dict, debug: bool = False) -> None:
    """Starts the grpc server.

    Args:
        properties (dict): The configuration of the server.
        debug (bool): Whether the server should be started in debug mode or not.
    """
    server = aio.server(
        futures.ThreadPoolExecutor(max_workers=10))  # TODO: How to determine how many workers? Guess?
    subtitles_pb2_grpc.add_SubtitleGeneratorServicer_to_server(
        servicer=SubtitleServerService(
            models=properties['vosk']['models'],
            receiver=f'{properties["receiver"]["host"]}:{properties["receiver"]["port"]}'),
        server=server)

    if debug:
        logging.debug('starting server with reflection activated.')
    service_names = (
        subtitles_pb2.DESCRIPTOR.services_by_name['SubtitleGenerator'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)

    port = properties['api']['port']
    logging.info(f'listening at :{port}')
    server.add_insecure_port(f'[::]:{port}')
    await server.start()
    await server.wait_for_termination()


def main():
    debug = os.getenv('DEBUG', '') != ""
    logging.basicConfig(level=(logging.INFO, logging.DEBUG)[debug])

    default_properties = {
        'api': {'port': 50055},
        'receiver': {'host': 'localhost', 'port': '50053'},
        'vosk': {'models': []},
    }

    try:
        properties = YAMLPropertiesFile(
            path=os.getenv("CONFIG_FILE", './config.yml'),
            default=default_properties
        ).get()
        properties = EnvProperties(default=properties).get()
        print(properties)
    except PropertyError as error:
        logging.error(error)
        sys.exit(1)

    asyncio.run(serve(properties, debug))


if __name__ == "__main__":
    main()
