import subprocess


class SubtitleGenerator:
    def __init__(self, model_path):
        self.__model_path = model_path

    def generate(self, input_path):
        # TODO: Wait for new VOSK release and change to python code
        _ = subprocess.call(['vosk-transcriber',
                               '--model', self.__model_path,
                               '-i', input_path,
                               '-t', 'srt', '-o', 'test.srt'])
