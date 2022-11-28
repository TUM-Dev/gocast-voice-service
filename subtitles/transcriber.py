from abc import ABC, abstractmethod


class Transcriber(ABC):
    @abstractmethod
    def generate(self, source: str, language: str) -> (str, str):
        """Generate and return (subtitles in VTT format, language) for parameter 'source'.

        Args:
            source: The path of the video file for which subtitles should be generated.
            language: The language of the transcribed video.
        """
        pass
