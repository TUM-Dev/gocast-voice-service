import io
from transcriber import Transcriber
import whisper
from whisper import utils

TIMESTAMP_FORMAT = "%02d:%02d:%06.3f"


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
                                        word_timestamps=True,
                                        logprob_threshold=None,
                                        no_speech_threshold=0.275,
                                        verbose=self.__verbose)
        language = result['language']

        vtt = io.StringIO()
        utils.WriteVTT('').write_result(result, vtt, {
            'max_line_width': 42,
            'max_line_count': 2,
            'highlight_words': False,
        })
        return vtt.getvalue(), language
