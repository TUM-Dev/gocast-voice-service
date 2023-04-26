import grpc
from concurrent import futures
import subtitles_pb2_grpc, subtitles_pb2
from google.protobuf import empty_pb2


class ReceiverService(subtitles_pb2_grpc.SubtitleReceiverServicer):
    """mock grpc service for the receiver side"""

    def __init__(self, save_to_file: bool):
        self.__save_to_file = save_to_file

    def Receive(self, req, context) -> empty_pb2:
        """ Handler function for an incoming Receive request. Adjust method as needed."""
        print(req)

        if self.__save_to_file:
            with open('test.srt', 'w') as file:
                file.write(req.subtitles)

        return empty_pb2.Empty()


def serve(port: int, save_to_file: bool = False) -> None:
    """Starts the grpc mock server."""
    print(f'receiver running @ localhost:{port}')

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    subtitles_pb2_grpc.add_SubtitleReceiverServicer_to_server(
        servicer=ReceiverService(save_to_file),
        server=server)

    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve(50053, True)
