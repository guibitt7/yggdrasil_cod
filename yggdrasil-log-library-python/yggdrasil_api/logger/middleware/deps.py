from starlette.requests import Request
from yggdrasil_api.logger.middleware.logger import YggApiLogger


def get_logger(request: Request) -> YggApiLogger:
    """Dependency para injetar o logger nas rotas FastAPI."""
    return request.state.logger


def get_trace_id(request: Request) -> str:
    """Dependency para injetar o trace_id nas rotas FastAPI."""
    return request.state.trace_id


def get_exec_id(request: Request) -> str:
    """Dependency para injetar o exec_id nas rotas FastAPI."""
    return request.state.exec_id
