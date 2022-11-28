import sys
import threading
import logging
import os
from properties import YAMLPropertiesFile, EnvProperties, PropertyError
from concurrent import futures
from grpc_reflection.v1alpha import reflection

from model_loader import download_models, ModelLoadError
import grpc
import subtitles_pb2
import subtitles_pb2_grpc
from vosk_transcriber import VoskTranscriber
from whisper_transcriber import WhisperTranscriber
from transcriber import Transcriber


class SubtitleServerService(subtitles_pb2_grpc.SubtitleGeneratorServicer):
    """grpc service for subtitles"""

    def __init__(self, transcriber: Transcriber, receiver: str) -> None:
        """Initialize service.

        Args:
            transcriber: The transcriber used for subtitle generation.
            receiver: The address of the receiver service.
        """
        self.__transcriber = transcriber
        self.__receiver = receiver

    def Generate(self, req: subtitles_pb2.GenerateRequest,
                 context: grpc.ServicerContext) -> subtitles_pb2.Empty:
        """ Handler function for an incoming Generate request.

        Args:
            req: An object holding the grpc message data.
            context: A context object passed to method implementations.
                Visit https://grpc.github.io/grpc/python/grpc.html#service-side-context for more information.

        Returns:
            subtitles_pb2.Empty
        """
        source: str = req.source_file
        language: str = req.language
        stream_id: str = req.stream_id

        logging.debug(f'checking if {source} exists')
        if not os.path.isfile(source):
            context.abort(grpc.StatusCode.NOT_FOUND, f'can not find source file: {source}')
            return subtitles_pb2.Empty()

        logging.debug('starting thread to generate subtitles')
        threading.Thread(target=self.__generate, args=(self.__transcriber, source, stream_id, language)).start()

        return subtitles_pb2.Empty()

    def __generate(self, transcriber: VoskTranscriber, source: str, stream_id: str, language: str) -> None:
        subtitles = transcriber.generate(source, language)
        logging.debug(f'stream_id={stream_id}; subtitles={subtitles[:32]}')

        logging.info(f'trying to connect to receiver @ {self.__receiver}')
        with grpc.insecure_channel(self.__receiver) as channel:
            stub = subtitles_pb2_grpc.SubtitleReceiverStub(channel)
            request = subtitles_pb2.ReceiveRequest(
                stream_id=stream_id,
                subtitles=subtitles,
                language=language)
            stub.Receive(request)


def serve(properties: dict, debug: bool = False) -> None:
    """Starts the grpc server.

    Args:
        properties: The configuration of the server.
        debug: Whether the server should be started in debug mode or not.
    """
    transcriber = get_transcriber(properties)
    receiver = f'{properties["receiver"]["host"]}:{properties["receiver"]["port"]}'

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))  # TODO: How to determine how many workers? Guess?
    subtitles_pb2_grpc.add_SubtitleGeneratorServicer_to_server(
        servicer=SubtitleServerService(transcriber, receiver),
        server=server)

    if debug:
        logging.debug(properties)
        logging.debug('starting server with reflection activated.')
        service_names = (
            subtitles_pb2.DESCRIPTOR.services_by_name['SubtitleGenerator'].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(service_names, server)

    port = properties['api']['port']
    logging.info(f'listening at :{port}')
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()


def get_transcriber(properties: dict) -> Transcriber:
    prop = properties['transcriber']
    if prop == 'whisper':
        return WhisperTranscriber(properties['whisper']['model'])
    if prop == 'vosk':
        models = [{'path': os.path.join(properties['vosk']['model_dir'], m['name']), 'lang': m['lang']}
                  for m in properties['vosk']['models']]
        return VoskTranscriber(models)


def main():
    debug = os.getenv('DEBUG', '') != ""
    logging.basicConfig(level=(logging.INFO, logging.DEBUG)[debug])

    properties = {
        'api': {'port': 50055},
        'receiver': {'host': 'localhost', 'port': '50053'},
        'transcriber': 'whisper',
        'vosk': {
            'model_dir': '/tmp',
            'download_urls': [],
            'models': []
        },
        'whisper': {'model': 'tiny'}
    }

    try:
        config_file = os.getenv("CONFIG_FILE")
        if config_file:
            if config_file.endswith('.yml'):
                properties = YAMLPropertiesFile(
                    path=config_file,
                    default=properties
                ).get()
            else:
                logging.error('unsupported config file type')
                sys.exit(1)

        properties = EnvProperties(default=properties).get()

        download_models(properties['vosk']['model_dir'], properties['vosk']['download_urls'])
    except PropertyError as propErr:
        logging.error(propErr)
        sys.exit(2)
    except ModelLoadError as modelLoadErr:
        logging.error(modelLoadErr)
        sys.exit(3)

    serve(properties, debug)


if __name__ == "__main__":
    main()