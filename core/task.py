import time
from enum import Enum
from typing import Optional
from typing import List

from queue import Queue

from ..utils.logger import log

from .info import ResultInfo
from .info import RecordInfo
from .info import Role
from .info import Event
from .info import WorkInfo

from .connector import BaseConnector


# 任务处理器标准
class TaskHandleSpec:

    @staticmethod
    def run(record_info: RecordInfo, result_info: ResultInfo = None):
        pass


# 任务流标准
class TaskFlowSpec:
    PRO_HANDLERS_CLS = []  # 前处理
    POST_HANDLERS_CLS = []  # 后处理
    CONNECTOR_CLS = None  # 连接器
    MAX_TIMEOUT: int = 300  # 最大超时时间
    MAX_RETRY_TIME: int = 7  # 最大重试次数
    RESULT_HANDLER_CLS: Optional[TaskHandleSpec] = None  # 结果处理器


class TaskFlowStatus(Enum):
    HANDLING = 1  # 待处理中
    EXECUTING = 2  # 待执行中
    COMPLETED = 3  # 已完成
    TERMINATED = 4  # 已终止


class TaskFlow:

    def __init__(self, record_info: RecordInfo):
        self.all_result_infos = []
        self.status: TaskFlowStatus = TaskFlowStatus.HANDLING
        self.record_info = record_info
        self.task_flow_spec: Optional[TaskFlowSpec] = None
        self.result_info = ResultInfo()
        self.is_pro = True  # 是否前处理
        self.run_num = 0
        self.every_time = []          # 每次耗时
        self.total_time = 0
        self.start_time = None

    def run(self):
        self.start_time = time.time()
        if self.status == TaskFlowStatus.HANDLING:
            self.handing()
        elif self.status == TaskFlowStatus.EXECUTING:
            self.executing()
        elif self.status == TaskFlowStatus.COMPLETED:
            pass
        else:
            self.total_time += 1
            pass

    def handing(self):
        if self.is_pro:
            pro_handlers_cls = self.task_flow_spec.PRO_HANDLERS_CLS
            for i, handler_cls in enumerate(pro_handlers_cls):
                if not issubclass(handler_cls, TaskHandleSpec):
                    log("not TaskHandleSpec")
                succeed = handler_cls.run(record_info=self.record_info)
                if succeed:
                    continue
                else:
                    self.status = TaskFlowStatus.TERMINATED
                    raise ValueError

            self.status = TaskFlowStatus.EXECUTING
            self.is_pro = False
        else:
            post_handlers_cls = self.task_flow_spec.POST_HANDLERS_CLS
            for i, handler_cls in enumerate(post_handlers_cls):
                if not issubclass(handler_cls, TaskHandleSpec):
                    log("not TaskHandleSpec")
                result_info = self.all_result_infos[-1]
                succeed = handler_cls.run(record_info=self.record_info, result_info=result_info)
                if succeed:
                    continue
                else:
                    self.status = TaskFlowStatus.TERMINATED
                    raise ValueError
            self.status = TaskFlowStatus.COMPLETED

    def executing(self):
        cls = self.task_flow_spec.CONNECTOR_CLS
        if not issubclass(cls, BaseConnector):
            raise ValueError

        connector = cls(uuid=self.record_info.uuid,
                        address_info=self.record_info.address_info,
                        account_info=self.record_info.account_info,
                        terminal_info=self.record_info.terminal_info)

        result_info = connector.send_cmd(command_info=self.record_info.command_info)
        self.all_result_infos.append(result_info)
        self.status = TaskFlowStatus.HANDLING

    def completed(self):
        pass


class TaskQueue:
    def __init__(self, work_info: WorkInfo, weight: int = 1, maxsize: int = 50, **kwargs):
        self.work_info = work_info
        self.weight = weight
        self.maxsize = maxsize
        self.confs = kwargs
        self.queue: Queue = Queue(maxsize=self.maxsize)

    @property
    def info(self):
        return {"weight": self.weight, "name": self.work_info.name}

    def get_ready(self):
        return True

    def put_ready(self):
        return True

    def get(self) -> Optional[TaskFlow]:
        if self.queue.empty():
            return None

        return self.queue.get()

    def put(self, task_flow: TaskFlow):
        if not isinstance(task_flow, TaskFlow):
            raise ValueError

        if self.queue.full():
            raise ValueError

        self.queue.put(task_flow)
        return True


# 滑动-按照时间限制流速
class SlideTaskQueue(TaskQueue):

    def __init__(self, work_info: WorkInfo, weight: int = 1, maxsize: int = 50, **kwargs):
        super().__init__(work_info, weight, maxsize, **kwargs)
        self.last_time_get = None
        self.last_time_put = None
        interval = self.confs.get("interval", 0.2)
        if isinstance(interval, int):
            self.interval = interval
        else:
            self.interval = 0.2

    def get_ready(self):
        now = time.time()
        if self.last_time_get is None:
            return True

        if now - self.last_time_get >= self.interval:
            return True
        else:
            return False


class TaskQueueManager:

    def __init__(self):
        self.queues_info = []
        self.queues_map = {}
        self.execute_queue = None
        self.handle_queue = None

    def add_queue(self, task_queue: TaskQueue):
        if task_queue.work_info.name in self.queues_map:
            log("已经存在")
            return None

        self.queues_map[task_queue.work_info.name] = task_queue
        self.queues_info.append(task_queue.info)

    def sort(self):
        # 队列根据权重排序
        self.queues_info.sort(key=lambda info: info["weight"])

    def filter(self, work_info: WorkInfo) -> List[TaskQueue]:
        filter_queues = []
        for info in self.queues_info:
            if info["name"] == work_info.name:
                filter_queues.append(self.queues_map[info["name"]])
        return filter_queues

    def get(self, work_info: WorkInfo) -> Optional[TaskFlow]:
        filter_queues = self.filter(work_info)
        for task_queue in filter_queues:
            if not task_queue.get_ready():
                continue

            return task_queue.get()
        return None

    def put(self, work_info: WorkInfo, task_flow: TaskFlow):
        if work_info.name not in self.queues_info:
            raise ValueError

        if not isinstance(task_flow, TaskFlow):
            raise ValueError

        if task_flow.status == TaskFlowStatus.HANDLING:
            pass


        pass


class TaskParser:
    pass
