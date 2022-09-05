import os
import subprocess
import threading
from os.path import normpath, basename


class SubtitleGenerator:
    """Generate Subtitles with a given model."""

    def __init__(self, model_path: str) -> None:
        """Initialize SubtitleGenerator with a given model.

        Args:
            model_path (str): The path to a language model provided by vosk.
                Visit https://alphacephei.com/vosk/models for a list of available models.
        """
        super().__init__()
        self.__model_path = model_path

    def get_model(self) -> str:
        """Return model name"""
        return basename(normpath(self.__model_path))

    def generate(self, source_file: str, destin_file: str) -> None:
        """Start a new thread and generate SRT content for parameter 'input_path'. Store at parameter 'destin_file'.

       Note:
           Waiting for next vosk-api release to remove subprocess call
           and implement SRT creation in python.

       Args:
            source_file (str): The path of the video file for which subtitles should be generated.
            destin_file (str): The path of the generated .srt file.
       """
        threading.Thread(
            target=self.__generate,
            args=(source_file, destin_file),
            daemon=False
        ).start()

    def __generate(self, input_path: str, output_path: str) -> None:
        _ = subprocess.call(['vosk-transcriber',
                             '--model', self.__model_path,
                             '-i', input_path,
                             '--log-level', 'WARN',
                             '-t', 'srt', '-o', output_path],
                            stdout=subprocess.PIPE)
