import sys
import logging
import os
from signal import signal, SIGTERM, SIGINT, SIGQUIT, strsignal

from concurrent.futures import ThreadPoolExecutor

import google

from properties import YAMLPropertiesFile, EnvProperties, PropertyError
from grpc_reflection.v1alpha import reflection
from grpc._channel import _InactiveRpcError

from google.protobuf import empty_pb2

from model_loader import download_models, ModelLoadError
import grpc
import subtitles_pb2
import subtitles_pb2_grpc
from vosk_transcriber import VoskTranscriber
from whisper_transcriber import WhisperTranscriber
from transcriber import Transcriber


class SubtitleServerService(subtitles_pb2_grpc.SubtitleGeneratorServicer):
    """grpc service for subtitles"""

    def __init__(self, transcriber: Transcriber, receiver: str, executor: ThreadPoolExecutor) -> None:
        """Initialize service.

        Args:
            transcriber: The transcriber used for subtitle generation.
            receiver: The address of the receiver service.
            executor: Threadpool for jobs.
        """
        self.__transcriber = transcriber
        self.__receiver = receiver
        self.__executor = executor

    def Generate(self, req: subtitles_pb2.GenerateRequest,
                 context: grpc.ServicerContext) -> empty_pb2.Empty:
        """ Handler function for an incoming Generate request.

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
        if not os.path.isfile(source):
            context.abort(grpc.StatusCode.NOT_FOUND, f'can not find source file: {source}')
            return empty_pb2.Empty()

        logging.debug('starting thread to generate subtitles')
        self.__executor.submit(self.__generate, self.__transcriber, source, stream_id, language)
        return empty_pb2.Empty()

    def __generate(self, transcriber: VoskTranscriber, source: str, stream_id: str, language: str) -> None:
        subtitles, language = transcriber.generate(source, language)

        logging.info(f'trying to connect to receiver @ {self.__receiver}')
        with grpc.insecure_channel(self.__receiver) as channel:
            stub = subtitles_pb2_grpc.SubtitleReceiverStub(channel)
            request = subtitles_pb2.ReceiveRequest(
                stream_id=stream_id,
                subtitles=subtitles,
                language=language)

            try:
                stub.Receive(request)
                logging.info('subtitle-request sent')
            except _InactiveRpcError as grpc_err:
                logging.error(grpc_err.details())
            except Exception as err:
                logging.error(err)


def serve(properties: dict, debug: bool = False) -> None:
    """Starts the grpc server.

    Args:
        properties: The configuration of the server.
        debug: Whether the server should be started in debug mode or not.
    """
    transcriber = get_transcriber(properties)
    receiver = f'{properties["receiver"]["host"]}:{properties["receiver"]["port"]}'
    port = properties['api']['port']

    with ThreadPoolExecutor(max_workers=10) as executor:  # TODO: How to determine how many workers? Guess?
        server = grpc.server(executor)
        subtitles_pb2_grpc.add_SubtitleGeneratorServicer_to_server(
            servicer=SubtitleServerService(transcriber, receiver, executor),
            server=server)

        if debug:
            logging.debug(properties)
            activate_reflection(server)

        logging.info(f'listening at :{port}')
        server.add_insecure_port(f'[::]:{port}')
        server.start()

        def handle_shutdown(signum, *_):
            logging.info(f'received "{strsignal(signum)}" signal')
            all_requests_done = server.stop(30)
            all_requests_done.wait(30)
            executor.shutdown(wait=True)
            logging.info('shut down gracefully')

        signal(SIGTERM, handle_shutdown)
        signal(SIGINT, handle_shutdown)
        signal(SIGQUIT, handle_shutdown)
        server.wait_for_termination()


def get_transcriber(properties: dict) -> Transcriber:
    prop = properties['transcriber']
    if prop == 'whisper':
        return WhisperTranscriber(properties['whisper']['model'])
    if prop == 'vosk':
        download_models(properties['vosk']['model_dir'], properties['vosk']['download_urls'])
        models = [{'path': os.path.join(properties['vosk']['model_dir'], m['name']), 'lang': m['lang']}
                  for m in properties['vosk']['models']]
        return VoskTranscriber(models)


def activate_reflection(server: grpc.Server) -> None:
    logging.debug('starting server with reflection activated.')
    service_names = (
        subtitles_pb2.DESCRIPTOR.services_by_name['SubtitleGenerator'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)


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
    except PropertyError as propErr:
        logging.error(propErr)
        sys.exit(2)
    except ModelLoadError as modelLoadErr:
        logging.error(modelLoadErr)
        sys.exit(3)

    serve(properties, debug)


if __name__ == "__main__":
    main()
