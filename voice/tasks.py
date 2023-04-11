from dataclasses import dataclass


@dataclass
class GenerationTask:
    source: str
    language: str
    stream_id: str


@dataclass
class ExtractAudioTask:
    source: str
    destination: str


class StopTask:
    pass
