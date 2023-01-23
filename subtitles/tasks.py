from dataclasses import dataclass


@dataclass
class GenerationTask:
    source: str
    language: str
    stream_id: str


class StopTask:
    pass
