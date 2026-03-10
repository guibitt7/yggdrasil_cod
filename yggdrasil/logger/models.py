import uuid
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class ParamsLogger:
    automation_name: str
    process_name: str
    exec_id: uuid.UUID = field(default_factory=uuid.uuid4)
    trace_id: uuid.UUID = field(default_factory=uuid.uuid4)
    fluid_id: int = 0
    impersonal_user: str = ""


class Colors:
    DEBUG = "\033[94m"
    INFO = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    CRITICAL = "\033[1;91m"
    RESET = "\033[0m"
    STEP = "\033[1;36m"


class LevelLogEnum(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StatusAutomationEnum(str, Enum):
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
