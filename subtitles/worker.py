import logging
from concurrent.futures import ThreadPoolExecutor
import subtitles_pb2
from tasks import GenerationTask, StopTask
from taskqueue import TaskQueue
from transcriber import Transcriber
from client import receive


class Worker:
    """Thread for subtitle generation"""

    def __init__(self,
                 transcriber: Transcriber,
                 receiver: str,
                 executor: ThreadPoolExecutor,
                 taskqueue: TaskQueue):
        """Start the generator threads."""
        executor.submit(run, transcriber, receiver, taskqueue)


def run(transcriber: Transcriber, receiver: str, taskqueue: TaskQueue) -> None:
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

    logging.info(f'worker: sending receive message to receiver @ {receiver}')
    receive(receiver,
            req=subtitles_pb2.ReceiveRequest(
                stream_id=task.stream_id,
                subtitles=subtitles,
                language=language))
