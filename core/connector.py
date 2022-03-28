from threading import Lock

from .info import AccountInfo
from .info import AddressInfo
from .info import TerminalInfo
from .info import CommandInfo
from .info import ResultInfo
from ..utils.logger import log


class BaseConnector:
    """
    # 基础链接器
    """
    # 存储实例化对象
    _instances = {}
    # 线程锁，保证线程下安全
    _lock: Lock = Lock()

    def __new__(cls, uuid: str, address_info: AddressInfo, account_info: AccountInfo,
                terminal_info: TerminalInfo, **kwargs):
        with cls._lock:
            if uuid in cls._instances:
                instance = cls._instances[uuid]
            else:
                instance = super().__new__(cls)
                cls._instances[uuid] = instance
        return instance

    def __init__(self, uuid: str, address_info: AddressInfo, account_info: AccountInfo,
                 terminal_info: TerminalInfo, **kwargs):
        self.uuid = uuid
        self.address_info = address_info
        self.account_info = account_info
        self.terminal_info = terminal_info
        self.kwargs = kwargs
        self.is_auth = False
        self.client = None

    def send_cmd(self, command_info: CommandInfo, **kwargs) -> ResultInfo:
        with self._lock:
            log(self, "Connector Send Command...", level='info')
            log(self, f"Command-category({command_info.category})",
                level='info')
            log_str = f"Command-id({command_info.uuid}), " \
                      f"Command-index({command_info.index}), " \
                      f"Command-content-start({command_info.content_des()})"
            log(self, log_str, level='info')
            func = self.option_func(command_info, "default")
            result_info = func(command_info, **kwargs)
        return result_info

    def map_func(self, func_name):
        if not hasattr(self, func_name):
            err = 'Your connector does not implement the corresponding ' \
                  f'sending instruction method. func name is [{func_name}].'
            raise ValueError(err)
        func = getattr(self, func_name)
        return func

    def option_func(self, command_info: CommandInfo, default_func: str):
        option_map = command_info.option_map
        if not option_map.strip():
            func_name = default_func
        else:
            func_name = option_map.lower()
        return self.map_func(func_name)






