import subprocess
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

    def generate(self, source: str, destination: str) -> None:
        """Generate SRT content for parameter 'input_path'. Store at parameter 'destin_file'.

       Note:
           Waiting for next vosk-api release to remove subprocess call
           and implement SRT creation in python.

       Args:
            source (str): The path of the video file for which subtitles should be generated.
            destination (str): The path of the generated .srt file.
       """
        _ = subprocess.call(['vosk-transcriber',
                             '--model', self.__model_path,
                             '-i', source,
                             '-t', 'srt',
                             '-o', destination])
