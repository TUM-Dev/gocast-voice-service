import subprocess
from vosk import Model, KaldiRecognizer, SetLogLevel
from transcriber import Transcriber


class VoskTranscriptionError(Exception):
    pass


class VoskTranscriber(Transcriber):
    SAMPLE_RATE = 16000

    def __init__(self, models: [object]) -> None:
        """Initialize VoskTranscriber with an array of given models.

        Args:
            models: Array of (language, model) tuples
                Visit https://alphacephei.com/vosk/models for a list of available models.
        """
        super().__init__()
        self.__recognizers = {
            model['lang']: new_recognizer(model['path'])
            for model in models}

    def generate(self, source: str, language: str) -> (str, str):
        with subprocess.Popen(['ffmpeg',
                               '-loglevel', 'quiet',
                               '-i', source,
                               '-ar', str(VoskTranscriber.SAMPLE_RATE),
                               '-ac', '1',
                               '-f', 'wav', "-"],
                              stdout=subprocess.PIPE).stdout as stream:
            if language in self.__recognizers:
                return srt_to_vtt(self.__recognizers[language].SrtResult(stream)), language
            else:
                raise VoskTranscriptionError(f'Unsupported language: {language}')


def set_vosk_log_level(debug: bool) -> None:
    if not debug:
        SetLogLevel(-1)


def new_recognizer(path: str):
    r = KaldiRecognizer(Model(model_path=path), VoskTranscriber.SAMPLE_RATE)
    r.SetWords(True)
    return r


def srt_to_vtt(srt: str) -> str:
    """Returns WebVTT string from SRT string"""
    return 'WEBVTT\n\n' + srt.replace(',', '.')
