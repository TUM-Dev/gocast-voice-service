from dataclasses import dataclass


@dataclass
class GenerationTask:
    source: str
    language: str
    stream_id: str


@dataclass
class ExtractAudioTask:
    source: str
    stream_id: str


class StopTask:
    pass
