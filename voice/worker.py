import logging
from concurrent.futures import ThreadPoolExecutor
import subtitles_pb2
from tasks import GenerationTask, StopTask, ExtractAudioTask
from taskqueue import TaskQueue
from transcriber import Transcriber
from client import receive
from voice.audio_functions import ffmpeg_video_to_hls_audio


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
        logging.debug(f'worker: task: {task}')
        if isinstance(task, GenerationTask):
            logging.info('worker: starting to generate subtitles...')
            generate(transcriber, receiver, task)
        if isinstance(task, ExtractAudioTask):
            logging.info('worker: starting to extract audio...')
            extract_audio(task)
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


def extract_audio(task: ExtractAudioTask) -> None:
    ffmpeg_video_to_hls_audio(task.source, task.destination)
