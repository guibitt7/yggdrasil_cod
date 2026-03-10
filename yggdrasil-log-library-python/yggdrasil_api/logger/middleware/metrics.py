# yggdrasil/logger/middleware/metrics.py
import time
from typing import Optional
from starlette.requests import Request
from yggdrasil_api.logger.middleware.models import LevelLogEnum, StatusApiEnum
from yggdrasil_api.logger.middleware.handlers.base_protocol import CounterResult


class RequestMetrics:
    def __init__(
        self, start_perf: float, status_code: int, exception_info: Optional[dict] = None
    ):
        self.duration_ms = int((time.perf_counter() - start_perf) * 1000)
        self._status_code = status_code
        self._exception_info = exception_info

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def level(self) -> LevelLogEnum:
        if self._status_code >= 500:
            return LevelLogEnum.CRITICAL
        if self._status_code >= 400:
            return LevelLogEnum.WARNING
        return LevelLogEnum.INFO

    @property
    def status(self) -> StatusApiEnum:
        return (
            StatusApiEnum.FAILED if self._status_code >= 400 else StatusApiEnum.SUCCESS
        )

    def build_extra(self, request: Request, db_data: CounterResult) -> dict:
        extra = {
            "method": request.method,
            "path": request.url.path,
            "status_code": self._status_code,
            "duration_ms": self.duration_ms,
            "client_ip": getattr(request.client, "host", "unknown"),
            "db_queries_count": db_data.count,
            "db_failed_count": db_data.failed_count,
        }
        if self._exception_info:
            extra.update(self._exception_info)
        return extra
