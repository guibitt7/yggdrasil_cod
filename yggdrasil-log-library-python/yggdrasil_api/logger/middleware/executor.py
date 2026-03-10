import traceback
from typing import Tuple, Optional
from fastapi import Response


class RequestExecutor:
    @staticmethod
    async def run(call_next, request) -> Tuple[int, Optional[Response], Optional[dict]]:
        try:
            response = await call_next(request)
            return response.status_code, response, None
        except Exception as exc:
            exception_info = {
                "exception": exc.__class__.__name__,
                "stacktrace": traceback.format_exc(),
            }
            return 500, None, exception_info
