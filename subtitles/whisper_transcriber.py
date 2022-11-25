from transcriber import Transcriber
import whisper


class WhisperTranscriber(Transcriber):
    def __init__(self, model: str) -> None:
        """Initialize WhisperTranscriber with an array of given models.

        Args:
            model: The model type.
                Visit https://github.com/openai/whisper for a list of available models.
        """
        super().__init__()
        self.__model = whisper.load_model(model)

    def generate(self, source: str, language: str = None) -> str:
        options = whisper.DecodingOptions(language=language)
        result = self.__model.transcribe(source, **options.__dict__, verbose=False)
        return result
