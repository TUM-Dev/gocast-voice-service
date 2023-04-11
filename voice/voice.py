import sys
import logging
import os
from signal import signal, SIGTERM, SIGINT, SIGQUIT, strsignal
from concurrent.futures import ThreadPoolExecutor
from properties import YAMLPropertiesFile, EnvProperties, PropertyError, DEFAULT_PROPERTIES
from grpc_reflection.v1alpha import reflection
from model_loader import download_models, ModelLoadError
import grpc
import audio_pb2_grpc
import subtitles_pb2
import subtitles_pb2_grpc
from audioservice import AudioService
from subtitleservice import SubtitleService
from taskqueue import TaskQueue
from vosk_transcriber import VoskTranscriber
from whisper_transcriber import WhisperTranscriber
from transcriber import Transcriber
from worker import Worker


def serve(executor: ThreadPoolExecutor,
          q: TaskQueue,
          port: int,
          debug: bool = False) -> None:
    """Starts the grpc server.

    Args:
        executor: The pool of threads
        q: Queue of tasks
        port: The port on which the voice service listens.
        debug: Whether the server should be started in debug mode or not.
    """
    server = grpc.server(executor)
    subtitles_pb2_grpc.add_SubtitleGeneratorServicer_to_server(
        servicer=SubtitleService(q),
        server=server)
    audio_pb2_grpc.add_AudioServicer_to_server(
        servicer=AudioService(q),
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
        q.stop()
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
    max_threads = properties['max_threads']
    cnt_workers = properties['cnt_workers']

    logging.debug(properties)

    q = TaskQueue(cnt_workers)
    with ThreadPoolExecutor(max_threads) as executor:
        [Worker(transcriber, receiver, executor, q) for _ in range(cnt_workers)]
        serve(executor, q, port, debug)


if __name__ == "__main__":
    main()
