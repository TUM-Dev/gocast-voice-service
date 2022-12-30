from transcriber import Transcriber
import whisper

SRT_TIMESTAMP_FORMAT = "%02d:%02d:%06.3f"


class WhisperTranscriber(Transcriber):
    def __init__(self, model: str, debug: bool) -> None:
        """Initialize WhisperTranscriber with an array of given models.

        Args:
            model: The model type.
                Visit https://github.com/openai/whisper for a list of available models.
            debug: Display debug information or not.
        """
        super().__init__()
        self.__model = model
        self.__verbose = (None, True)[debug]

    def generate(self, source: str, language: str = None) -> (str, str):
        options = whisper.DecodingOptions(language=language)
        transcriber = whisper.load_model(self.__model)

        # solve silence issue. see: https://github.com/openai/whisper/discussions/29
        result = transcriber.transcribe(source,
                                        **options.__dict__,
                                        logprob_threshold=None,
                                        no_speech_threshold=0.275,
                                        verbose=self.__verbose)
        language = result['language']

        return _whisper_to_vtt(result['segments']), language


def _whisper_to_vtt(segments) -> str:
    """Return WebVTT subtitle string"""
    vtt = ['WEBVTT\n']

    for i, s in enumerate(segments):
        time_start, time_end = s['start'], s['end']
        timestamp_start = SRT_TIMESTAMP_FORMAT % _get_hms(time_start)
        timestamp_end = SRT_TIMESTAMP_FORMAT % _get_hms(time_end)

        vtt.append(f'{i + 1}')
        vtt.append(f'{timestamp_start} --> {timestamp_end}')
        vtt.append(s['text'].strip() + "\n")

    return '\n'.join(vtt)


def _get_hms(time: float) -> (float, float, float):
    return int(time / 3600), (time / 60) % 60, time % 60
