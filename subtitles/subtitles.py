import queue
import sys
import logging
import os
from signal import signal, SIGTERM, SIGINT, SIGQUIT, strsignal
from concurrent.futures import ThreadPoolExecutor
from properties import YAMLPropertiesFile, EnvProperties, PropertyError, DEFAULT_PROPERTIES
from grpc_reflection.v1alpha import reflection
from google.protobuf import empty_pb2
from model_loader import download_models, ModelLoadError
import grpc
import subtitles_pb2
import subtitles_pb2_grpc
from vosk_transcriber import VoskTranscriber
from whisper_transcriber import WhisperTranscriber
from transcriber import Transcriber
from tasks import GenerationTask, StopTask
from generator import Generator


class SubtitleServerService(subtitles_pb2_grpc.SubtitleGeneratorServicer):
    """grpc service for subtitles"""

    def __init__(self, queue: queue.Queue) -> None:
        """Initialize service"""
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
        if not os.path.isfile(source):
            context.abort(grpc.StatusCode.NOT_FOUND, f'can not find source file: {source}')
            return

        logging.debug('enqueue request')
        self.__queue.put(GenerationTask(source, language, stream_id))

        return empty_pb2.Empty()


def serve(executor: ThreadPoolExecutor,
          q: queue.Queue,
          port: int,
          debug: bool = False) -> None:
    """Starts the grpc server.

    Args:
        executor: The pool of threads
        q: Queue of generator tasks
        port: The port on which the voice service listens.
        debug: Whether the server should be started in debug mode or not.
    """
    server = grpc.server(executor)
    subtitles_pb2_grpc.add_SubtitleGeneratorServicer_to_server(
        servicer=SubtitleServerService(q),
        server=server)

    if debug:
        activate_reflection(server)

    logging.info(f'listening at :{port}')
    server.add_insecure_port(f'[::]:{port}')
    server.start()

    def handle_shutdown(signum, *_):
        logging.info(f'received "{strsignal(signum)}" signal')
        all_requests_done = server.stop(16)
        all_requests_done.wait(16)
        q.put(StopTask())
        executor.shutdown(wait=True)
        logging.info('shut down gracefully')

    signal(SIGTERM, handle_shutdown)
    signal(SIGINT, handle_shutdown)
    signal(SIGQUIT, handle_shutdown)
    server.wait_for_termination()


def get_transcriber(properties: dict, debug: bool) -> Transcriber:
    prop = properties['transcriber']
    if prop == 'whisper':
        return WhisperTranscriber(properties['whisper']['model'], debug)
    if prop == 'vosk':
        download_models(properties['vosk']['model_dir'], properties['vosk']['download_urls'])
        models = [{'path': os.path.join(properties['vosk']['model_dir'], m['name']), 'lang': m['lang']}
                  for m in properties['vosk']['models']]
        return VoskTranscriber(models, debug)


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

    properties = DEFAULT_PROPERTIES

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

    transcriber = get_transcriber(properties, debug)
    receiver = f'{properties["receiver"]["host"]}:{properties["receiver"]["port"]}'
    port = properties['api']['port']
    max_workers = properties['max_workers']

    logging.debug(properties)

    q = queue.Queue()
    with ThreadPoolExecutor(max_workers) as executor:
        Generator(transcriber, receiver, executor, q)
        serve(executor, q, port, debug)


if __name__ == "__main__":
    main()
