import queue

from tasks import StopTask


class TaskQueue(queue.Queue):
    def __init__(self, task_worker_cnt: int = 1):
        super().__init__()
        self.task_worker_cnt = task_worker_cnt

    def stop(self):
        for _ in range(self.task_worker_cnt):
            self.put(StopTask())