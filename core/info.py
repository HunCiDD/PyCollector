import copy
from typing import Any
from hashlib import sha256
from enum import Enum


# 生成信息Info的唯一标识uuid
class UUIDInfo:
    def __init__(self, hash_value):

        self._hash_value = hash_value
        self._uuid = sha256(f'{self._hash_value}'.encode()).hexdigest()

    @property
    def hash_value(self) -> str:
        return self._hash_value

    @property
    def uuid(self) -> str:
        return self._uuid


class AccountInfo:

    def __init__(self, username: str, password: str, **kwargs):
        self._username = username
        self._password = password
        self.kwargs = kwargs

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    @property
    def des(self):
        return f"{self._username}"


class AddressInfo:
    def __init__(self, hostname: str, port: str, **kwargs):
        self._hostname = hostname
        self._port = port
        self.kwargs = kwargs

    @property
    def hostname(self):
        return self._hostname

    @property
    def port(self):
        return self._port

    @property
    def des(self):
        return f"{self._hostname}:{self._port}"


class TerminalInfo:
    def __init__(self, name: str, version: str, **kwargs):
        self.name = name
        self.version = version
        self.kwargs = kwargs

    @property
    def des(self):
        return f"{self.name}:{self.version}"


class PtlCategory(Enum):
    TCP = 8080
    UDP = 8081
    HTTP = 80
    HTTPS = 443
    OTHER = 0


PtlCategoryList = [i for i, _ in PtlCategory.__members__.items()]


class ProtocolInfo:
    def __init__(self, category: PtlCategory = PtlCategory.OTHER,
                 name: str = '', version: str = '', **kwargs):
        self.category = category
        self.name = name
        self.version = version
        self.kwargs = kwargs

    @property
    def des(self):
        return f"{self.category.name}:{self.name}:{self.version}"


class CmdCategory(Enum):
    OTHER = 0
    BUILT_IN = 1
    SHELL_SCRIPT = 11
    PYTHON_SCRIPT = 12
    SQL = 22


CmdCategoryList = [i for i, _ in CmdCategory.__members__.items()]


# 命令信息
class CommandInfo(UUIDInfo):
    OPTION_START_TAG = '#['
    OPTION_END_TAG = ']'

    def __init__(self, category: CmdCategory = CmdCategory.OTHER,
                 content: str = '', params: dict = None, **kwargs):
        self.category = category
        self._content = content.strip()
        self._params = params  # 命令参数
        if self._params is None:
            self._params = {}
        self.kwargs = kwargs
        self.index = str(self.kwargs.get("index", 0))
        self._option = str(self.kwargs.get("option", ""))
        super().__init__(f"{self._content}:{self._params}")
        self.option_map = self._option_map()

    @property
    def option(self):
        return self._option

    @option.setter
    def option(self, value):
        if isinstance(value, str):
            self._option = value

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value: str):
        self._content = str(value).strip()

    def content_des(self):
        if len(self._content) >= 10:
            return self._content[0:10]
        else:
            return self._content[0: len(self._content)]

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, value):
        if isinstance(value, dict):
            self._params = value

    # 获取内部映射
    def _option_map(self) -> str:
        if self._option.startswith(self.OPTION_START_TAG) \
                and self._option.endswith(self.OPTION_END_TAG):
            option = self.option
            option = option.lstrip(self.OPTION_START_TAG).rstrip(self.OPTION_END_TAG)
            option = '_'.join([i.upper() for i in option.split(' ') if i])
        else:
            option = ''
        return option


class RstStatus(Enum):
    SUCCESS = 1
    FAILED = 2
    ABNORMAL = 3


RstStatusList = [i for i, _ in RstStatus.__members__.items()]


class ResultInfo:
    def __init__(self, category: RstStatus = RstStatus.FAILED,
                 code: int = 0, msg: str = '', data: Any = None):
        self.category = category
        self.code = code
        self.msg = msg
        self.data = data

    @property
    def err_msg(self):
        return f'{self.category.name}[{self.code}]:{self.msg}'


class RecordInfo(UUIDInfo):
    def __init__(self, account_info: AccountInfo, address_info: AddressInfo,
                 terminal_info: TerminalInfo, protocol_info: ProtocolInfo,
                 command_info: CommandInfo, **kwargs):
        self.account_info = account_info
        self.address_info = address_info
        self.terminal_info = terminal_info
        self.protocol_info = protocol_info
        self.command_info = command_info
        self.kwargs = kwargs
        hash_value = f"{self.address_info.des}/{self.account_info.des}" \
                     f"{self.terminal_info.des}/{self.protocol_info.des}"
        super().__init__(hash_value)


class Role(Enum):
    Leader = 1
    Follower = 2


class Event(Enum):
    INIT = 0        # 初始化
    HANDLE = 1      # 处理
    EXECUTE = 2     # 执行
    SUMMARY = 3     # 汇总


class WorkInfo:
    def __init__(self, role: Role = Role.Follower, event: Event = Event.HANDLE):
        self.role = role
        self.event = event

    @property
    def name(self):
        return f"{self.role.name}:{self.event.name}"
