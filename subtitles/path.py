import os

import grpc
import urllib3


class InvalidPathException(Exception):
    def __init__(self, code: grpc.StatusCode, *args):
        super().__init__(args)
        self.grpc_code = code


def file_exists(file_path: str):
    if file_path.startswith("https://"):
        http = urllib3.PoolManager()
        try:
            r = http.request('GET', file_path)
        except urllib3.exceptions.HTTPError:
            raise InvalidPathException(grpc.StatusCode.NOT_FOUND, f'source url unavailable: {file_path}')
        if r.status != 200:
            raise InvalidPathException(grpc.StatusCode.NOT_FOUND,
                                       f'source url replies with status {r.status}: {file_path}')
    elif not os.path.isfile(file_path):
        raise InvalidPathException(grpc.StatusCode.NOT_FOUND, f'can not find source file: {file_path}')


def dir_exists(path: str):
    if not os.path.isdir(path):
        raise InvalidPathException(grpc.StatusCode.NOT_FOUND, f'invalid path: {path}')
