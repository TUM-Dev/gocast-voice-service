import subprocess
import tempfile
from os.path import normpath, basename
from vosk import Model, KaldiRecognizer

SAMPLE_RATE = 16000


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
        self.__recognizer = KaldiRecognizer(Model(model_path=model_path), SAMPLE_RATE)
        self.__recognizer.SetWords(True)

    def get_model(self) -> str:
        """Return model name"""
        return basename(normpath(self.__model_path))

    def get_language(self) -> str:
        """Return language of generator"""
        return 'en'  # TODO: Change to real language

    def generate(self, source: str) -> str:
        """Generate and return SRT content for parameter 'source'.

       Args:
            source (str): The path of the video file for which subtitles should be generated.
       """
        with subprocess.Popen(['ffmpeg',
                               '-loglevel', 'quiet',
                               '-i', source,
                               '-ar', str(SAMPLE_RATE),
                               '-ac', '1',
                               '-f', 'wav', "-"],
                              stdout=subprocess.PIPE).stdout as stream:
            return self.__recognizer.SrtResult(stream)
