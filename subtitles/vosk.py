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
        self.__model_path = model_path

    def get_model(self) -> str:
        """Return model name"""
        return basename(normpath(self.__model_path))

    def generate(self, input_path: str) -> str:
        """Generate SRT content for input parameter 'input_path'.

        Note:
            Waiting for next vosk-api release to remove subprocess call
            and implement SRT creation in python.

        Args:
             input_path (str): The path of the video file for which subtitles should be generated.

        Returns:
            string containing the generated subtitles in SRT format
        """
        _ = subprocess.call(['vosk-transcriber',
                             '--model', self.__model_path,
                             '-i', input_path,
                             '-t', 'srt', '-o', 'tmp.srt'],
                            stdout=subprocess.PIPE)

        with open('tmp.srt', 'r') as file:
            srt = file.read()

        return srt
