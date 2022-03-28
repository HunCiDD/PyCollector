
from enum import Enum
from typing import Optional
from threading import Thread

from .info import Role
from .info import Event
from .info import WorkInfo
from .task import TaskFlowStatus
from .task import TaskFlow
from .task import TaskQueueManager


class Worker(Thread):
    def __init__(self, name: str, work_info: WorkInfo,
                 queue_manager: TaskQueueManager, **kwargs):
        super().__init__()
        self.name = name
        self.work_info = work_info
        self.queue_manager = queue_manager
        self.kwargs = kwargs

    def run(self) -> None:
        while True:
            task_flow = self.queue_manager.get(self.work_info)
            if task_flow is None:
                continue

            if not isinstance(task_flow, TaskFlow):
                continue

            task_flow.run()
            if task_flow.status == TaskFlowStatus.EXECUTING:
                self.queue_manager.put(task_flow, self.role)



        pass