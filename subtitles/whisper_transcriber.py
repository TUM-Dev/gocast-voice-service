from transcriber import Transcriber
import whisper

SRT_TIMESTAMP_FORMAT = "%02d:%02d:%06.3f"


class WhisperTranscriber(Transcriber):
    def __init__(self, model: str) -> None:
        """Initialize WhisperTranscriber with an array of given models.

        Args:
            model: The model type.
                Visit https://github.com/openai/whisper for a list of available models.
        """
        super().__init__()
        self.__model = whisper.load_model(model)

    def generate(self, source: str, language: str = None) -> (str, str):
        # solve silence issue. see: https://github.com/openai/whisper/discussions/29
        options = whisper.DecodingOptions(language=language).__dict__.copy()
        options['no_speech_threshold'] = 0.275
        options['logprob_threshold'] = None

        result = self.__model.transcribe(source, **options, verbose=False)
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
