import subprocess
from concurrent import futures
import grpc
import subtitles_pb2
import subtitles_pb2_grpc
from grpc_reflection.v1alpha import reflection


class SubtitleService(subtitles_pb2_grpc.SubtitlesServicer):

    def Generate(self, request, context):
        return subtitles_pb2.GenerateSubtitlesResponse(path=request.path)


def serve(debug: bool = False):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    subtitles_pb2_grpc.add_SubtitlesServicer_to_server(SubtitleService(), server)

    if debug:
        service_names = (
            subtitles_pb2.DESCRIPTOR.services_by_name['Subtitles'].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(service_names, server)

    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


class SubtitleGenerator:
    def __init__(self, model, input, output):
        self.__in_path = input
        self.__out_path = output
        self.__model_path = model

    def generate(self):
        # TODO: Wait for new VOSK release and change to python code
        var = subprocess.call(['vosk-transcriber',
                               '--model', self.__model_path,
                               '-i', self.__in_path,
                               '-t', 'srt', '-o', self.__out_path],
                              stdout=subprocess.PIPE)
        print(var)


if __name__ == "__main__":
    serve(debug = True)
