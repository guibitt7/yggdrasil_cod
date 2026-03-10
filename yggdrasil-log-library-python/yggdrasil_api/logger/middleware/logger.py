from json import dumps
import sys
from datetime import datetime, timezone
from yggdrasil_api.logger.middleware.models import (
    ApiRequestParams,
    LevelLogEnum,
    StatusApiEnum,
)


class YggApiLogger:
    def __init__(self, params: ApiRequestParams):
        self.params = params

    def log(
        self,
        level: LevelLogEnum,
        msg: str,
        status: StatusApiEnum = StatusApiEnum.SUCCESS,
        **kwargs,
    ) -> None:
        # Ordem pensada para performance de indexação no Loki/Elastic
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.value,
            "app": self.params.app_name,
            "version": self.params.version,
            "trace_id": self.params.trace_id,
            "status": status.value,
            "message": msg,
            **kwargs,
        }
        # default=str garante que objetos complexos (como UUID ou Datetime) não quebrem o JSON
        sys.stdout.write(dumps(payload, default=str) + "\n")
        sys.stdout.flush()

    def info(self, msg: str, **kwargs) -> None:
        self.log(LevelLogEnum.INFO, msg, StatusApiEnum.SUCCESS, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        # Warning geralmente é um sucesso parcial ou algo que não impediu a execução
        self.log(LevelLogEnum.WARNING, msg, StatusApiEnum.SUCCESS, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        self.log(LevelLogEnum.ERROR, msg, StatusApiEnum.FAILED, **kwargs)

    def critical(self, msg: str, **kwargs) -> None:
        self.log(LevelLogEnum.CRITICAL, msg, StatusApiEnum.FAILED, **kwargs)

    def debug(
        self, msg: str, status: StatusApiEnum = StatusApiEnum.SUCCESS, **kwargs
    ) -> None:
        self.log(LevelLogEnum.DEBUG, msg, status, **kwargs)
