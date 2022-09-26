import subprocess
import tempfile
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

    def get_language(self) -> str:
        return 'en'  # TODO: Change to real language

    def generate(self, source: str) -> str:
        """Generate and return SRT content for parameter 'input_path'.

       Note:
           Waiting for next vosk-api release to remove subprocess call
           and implement SRT creation in python.

       Args:
            source (str): The path of the video file for which subtitles should be generated.
       """
        with tempfile.NamedTemporaryFile() as tmp:
            _ = subprocess.call(['vosk-transcriber',
                                 '--model', self.__model_path,
                                 '-i', source,
                                 '-t', 'srt',
                                 '-o', tmp.name])

            subtitles = tmp.read()
            return subtitles
