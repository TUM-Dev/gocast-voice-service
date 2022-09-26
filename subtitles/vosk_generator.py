import logging
import subprocess
import tempfile
from os.path import normpath, basename
from vosk import Model, KaldiRecognizer

SAMPLE_RATE = 16000


class SubtitleGenerator:
    """Generate Subtitles with a given model."""

    def __init__(self, model_path: str, model_lang: str) -> None:
        """Initialize SubtitleGenerator with a given model.

        Args:
            model_path (str): The path to a language model provided by vosk.
                Visit https://alphacephei.com/vosk/models for a list of available models.
        """
        super().__init__()
        self.__model_path = model_path
        self.__model_lang = model_lang
        self.__recognizer = KaldiRecognizer(Model(model_path=model_path), SAMPLE_RATE)
        self.__recognizer.SetWords(True)

    def get_language(self) -> str:
        """Return language of generator"""
        return self.__model_lang

    def generate(self, source: str) -> str:
        """Generate and return VTT content for parameter 'source'.

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
            return self.__srt_to_vtt(self.__recognizer.SrtResult(stream))

    def __srt_to_vtt(self, srt: str) -> str:
        """Returns WebVTT string from SRT string"""
        return 'WEBVTT\n\n' + srt.replace(',', '.')