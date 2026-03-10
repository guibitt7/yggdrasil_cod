# yggdrasil/logger/middleware/models.py
import uuid
from enum import Enum
from dataclasses import dataclass, field


class LevelLogEnum(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StatusApiEnum(str, Enum):
    SUCCESS = "SUCCESS"  # 2xx
    FAILED = "FAILED"  # 4xx / 5xx
    PROCESSING = "PROCESSING"  # Requisição ainda em andamento


@dataclass
class ApiRequestParams:
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    app_name: str = "unnamed-api"
    version: str = "0.0.0"
    user: str = "anonymous"
