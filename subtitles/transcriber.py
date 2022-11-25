from abc import ABC, abstractmethod


class TranscriberFactory(ABC):
    def make(self):
        pass


class Transcriber(ABC):
    @abstractmethod
    def generate(self, source: str, language: str) -> str:
        """Generate and return VTT content for parameter 'source'.

        Args:
            source: The path of the video file for which subtitles should be generated.
            language: The language of the transcribed video.
        """
        pass
