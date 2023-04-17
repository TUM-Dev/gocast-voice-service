import logging
import os.path
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import subtitles_pb2
from tasks import GenerationTask, StopTask, ExtractAudioTask
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
        if isinstance(task, ExtractAudioTask):
            logging.info('worker: starting to extract audio...')
            logging.debug(f'worker: task: {task}')
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
    playlist = os.path.join(task.destination, Path(task.source).stem + '.m3u8')
    segment_filename = os.path.join(task.destination, 'segment%04d.ts')

    subprocess.Popen(['ffmpeg',
                      '-y',
                      '-i', task.source,
                      '-c:a', 'aac',
                      '-f', 'hls',
                      '-hls_time', '8',
                      '-hls_playlist_type', 'vod',
                      '-hls_flags', 'independent_segments',
                      '-hls_segment_type', 'mpegts',
                      '-hls_segment_filename', segment_filename,
                      '-vn',
                      playlist])
