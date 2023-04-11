import os

import grpc
import urllib3


class InvalidPathException(Exception):
    def __init__(self, code: grpc.StatusCode, *args):
        super().__init__(args)
        self.grpc_code = code


def is_valid_path(path: str):
    if path.startswith("https://"):
        http = urllib3.PoolManager()
        try:
            r = http.request('GET', path)
        except urllib3.exceptions.HTTPError:
            raise InvalidPathException(grpc.StatusCode.NOT_FOUND, f'source url unavailable: {path}')
        if r.status != 200:
            raise InvalidPathException(grpc.StatusCode.NOT_FOUND, f'source url replies with status {r.status}: {path}')
    elif not os.path.isfile(path):
        raise InvalidPathException(grpc.StatusCode.NOT_FOUND, f'can not find source file: {path}')
