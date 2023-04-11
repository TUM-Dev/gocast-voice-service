"""Implements gRPC Client facade"""

import logging
import grpc
import subtitles_pb2_grpc
import subtitles_pb2
from grpc._channel import _InactiveRpcError


def receive(receiver: str, req: subtitles_pb2.ReceiveRequest):
    with grpc.insecure_channel(receiver) as channel:
        stub = subtitles_pb2_grpc.SubtitleReceiverStub(channel)
        try:
            stub.Receive(req)
        except _InactiveRpcError as grpc_err:
            logging.error(grpc_err.details())
        except Exception as err:
            logging.error(err)
