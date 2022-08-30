from concurrent import futures
import grpc
import subtitles_pb2
import subtitles_pb2_grpc
from grpc_reflection.v1alpha import reflection
import logging
from config import Config
import os
import vosk


class SubtitleService(subtitles_pb2_grpc.SubtitlesServicer):
    def __init__(self, model_paths: [str]):
        logging.debug(f'loading SubtitleService with models: {model_paths}')
        self.__generators = [vosk.SubtitleGenerator(path) for path in model_paths]

    def Generate(self, request, context):
        for i, gen in enumerate(self.__generators):
            logging.debug(f'{i}: generating subtitles for {request.path}')
            gen.generate(request.path)
        return subtitles_pb2.GenerateSubtitlesResponse(path=request.path)


def serve(cfg: Config, debug: bool = False):
    logging.basicConfig(level=(logging.INFO, logging.DEBUG)[debug])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service = SubtitleService(
        model_paths=cfg['vosk']['models']
    )
    subtitles_pb2_grpc.add_SubtitlesServicer_to_server(service, server)

    if debug:
        logging.debug('starting server with reflection activated.')
        service_names = (
            subtitles_pb2.DESCRIPTOR.services_by_name['Subtitles'].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(service_names, server)

    port = cfg['api']['port']
    logging.info(f'listening at :{port}')
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve(
        cfg=Config(os.environ["CONFIG_FILE"]),
        debug=os.environ["DEBUG"] != ""
    )
