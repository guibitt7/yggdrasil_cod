from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from yggdrasil_api.logger.middleware.context import RequestContext
from yggdrasil_api.logger.middleware.metrics import RequestMetrics
from yggdrasil_api.logger.middleware.logger import YggApiLogger
from yggdrasil_api.logger.middleware.handlers.factory import DBHandlerFactory
from yggdrasil_api.logger.middleware.handlers.response import YggResponseProcessor
from yggdrasil_api.logger.middleware.executor import RequestExecutor
from yggdrasil_api.logger.middleware.handlers.base_protocol import CounterResult


_IGNORED_PATHS = {"/health", "/metrics", "/ping", "/favicon.ico"}


class YggApiMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, app_name: str, version: str = "0.0.0", db=None):
        super().__init__(app)
        self.app_name = app_name
        self.version = version
        self.db_handler = DBHandlerFactory.create(db) if db else None

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _IGNORED_PATHS:
            return await call_next(request)

        return await self._execute_monitored_request(request, call_next)

    async def _execute_monitored_request(self, request, call_next) -> Response:
        context = RequestContext(request, self.app_name, self.version)
        self._inject_state(request, context)

        code, resp, exc = await RequestExecutor.run(call_next, request)

        self._finalize_logging(request, context, code, exc)
        return YggResponseProcessor(context.trace_id).process(resp) if resp else None

    def _inject_state(self, request, context):
        request.state.logger = YggApiLogger(context.build_params())
        request.state.trace_id = context.trace_id

    def _finalize_logging(self, request, context, code, exc):
        db_data = self.db_handler.reset() if self.db_handler else CounterResult(0)

        metrics = RequestMetrics(context.start_perf, code, exc)
        extra = metrics.build_extra(request, db_data) 

        request.state.logger.log(
            level=metrics.level,
            msg=f"{request.method} {request.url.path} → {code}",
            status=metrics.status,
            **extra,
        )
