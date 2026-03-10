import uuid
from uuid import uuid4, UUID
import time
from starlette.requests import Request
from yggdrasil_api.logger.middleware.models import ApiRequestParams


class RequestContext:
    def __init__(self, request: Request, app_name: str, version: str):
        raw_trace_id = request.headers.get("X-Trace-Id")
        self.trace_id = (
            raw_trace_id if self._is_valid_uuid(raw_trace_id) else str(uuid4())
        )
        self.app_name = app_name
        self.version = version
        self.user = request.headers.get("X-User", "anonymous")
        self.start_perf = time.perf_counter()

    def build_params(self) -> ApiRequestParams:
        return ApiRequestParams(
            trace_id=self.trace_id,
            app_name=self.app_name,
            version=self.version,
            user=self.user,
        )

    @staticmethod
    def _is_valid_uuid(value: str | None) -> bool:
        if not value:
            return False
        try:
            UUID(value)
            return True
        except ValueError:
            return False
