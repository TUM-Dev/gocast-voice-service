import subprocess
from concurrent import futures
import grpc
import subtitles_pb2
import subtitles_pb2_grpc
from grpc_reflection.v1alpha import reflection
import logging


class SubtitleService(subtitles_pb2_grpc.SubtitlesServicer):
    def __init__(self, model_path: str):
        self.__generator = SubtitleGenerator(model_path)

    def Generate(self, request, context):
        self.__generator.generate(request.path)
        return subtitles_pb2.GenerateSubtitlesResponse(path=request.path)


def serve(debug: bool = False, port: str = '50051'):
    logging.basicConfig(level=(logging.INFO, logging.DEBUG)[debug])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service = SubtitleService(
        model_path="../vosk-model-en-us-0.22/"
    )
    subtitles_pb2_grpc.add_SubtitlesServicer_to_server(service, server)

    if debug:
        logging.debug("starting server with reflection activated.")
        service_names = (
            subtitles_pb2.DESCRIPTOR.services_by_name['Subtitles'].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(service_names, server)

    logging.info(f"server listening at :{port}")
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()


class SubtitleGenerator:
    def __init__(self, model_path):
        self.__model_path = model_path

    def generate(self, input_path):
        # TODO: Wait for new VOSK release and change to python code
        print('start generation')
        var = subprocess.call(['vosk-transcriber',
                               '--model', self.__model_path,
                               '-i', input_path,
                               '-t', 'srt', '-o', 'test.srt'])
        print(var)


if __name__ == "__main__":
    serve(debug=True)
