import logging
import queue

import subtitles_pb2, subtitles_pb2_grpc
import grpc
from grpc._channel import _InactiveRpcError
from concurrent.futures import ThreadPoolExecutor
from transcriber import Transcriber
from tasks import GenerationTask, StopTask


class Generator:
    """Thread for subtitle generation"""

    def __init__(self,
                 transcriber: Transcriber,
                 receiver: str,
                 executor: ThreadPoolExecutor,
                 taskqueue: queue.Queue):
        """Start the generator threads."""
        executor.submit(run, transcriber, receiver, taskqueue)


def run(transcriber: Transcriber, receiver: str, taskqueue: queue.Queue):
    while True:
        logging.info('worker: waiting for task...')
        task = taskqueue.get()
        if isinstance(task, GenerationTask):
            logging.info('worker: starting to generate subtitles...')
            logging.debug(f'worker: task: {task}')
            generate(transcriber, receiver, task)
        elif isinstance(task, StopTask):
            break


def generate(transcriber: Transcriber, receiver: str, task: GenerationTask) -> None:
    subtitles, language = transcriber.generate(task.source, task.language)

    logging.info(f'worker: trying to connect to receiver @ {receiver}')
    with grpc.insecure_channel(receiver) as channel:
        stub = subtitles_pb2_grpc.SubtitleReceiverStub(channel)
        request = subtitles_pb2.ReceiveRequest(
            stream_id=task.stream_id,
            subtitles=subtitles,
            language=language)

        try:
            stub.Receive(request)
            logging.info('worker: subtitle-request sent')
        except _InactiveRpcError as grpc_err:
            logging.error(grpc_err.details())
        except Exception as err:
            logging.error(err)
