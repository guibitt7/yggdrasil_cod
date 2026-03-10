from datetime import datetime, timezone
from yggdrasil.logger.models import ParamsLogger, LevelLogEnum, StatusAutomationEnum
from yggdrasil.logger.writer import LogWriter


class YggLogger:
    def __init__(self, params_logger: ParamsLogger):
        self._params = params_logger
        self.start_time = datetime.now(timezone.utc).isoformat()
        self._writer = LogWriter(params_logger, self.start_time)

    def log_start(self, step: str = "Iniciando processo"):
        payload = self._writer.build(
            LevelLogEnum.INFO,
            StatusAutomationEnum.STARTED,
            step,
            f"Automação {self._params.automation_name} iniciada",
        )
        self._writer.write(payload)
        self._writer.pretty(
            LevelLogEnum.INFO, StatusAutomationEnum.STARTED, step, payload
        )

    def log_finish(
        self, status: StatusAutomationEnum, step: str, msg: str, error_type: str = None
    ):
        time_finish = datetime.now(timezone.utc)
        duration_ms = int(
            (time_finish - datetime.fromisoformat(self.start_time)).total_seconds()
            * 1000
        )
        level = (
            LevelLogEnum.INFO
            if status == StatusAutomationEnum.SUCCESS
            else LevelLogEnum.CRITICAL
        )

        payload = self._writer.build(
            level,
            status,
            step,
            msg or f"Automação finalizada com status {status}",
            end_time=time_finish.isoformat(),
            duration_ms=duration_ms,
            error_type=error_type,
        )
        self._writer.write(payload)
        self._writer.pretty(level, status, step, msg)

    def log(self, level: LevelLogEnum, step: str, msg: str, **extra):
        status_map = {
            LevelLogEnum.DEBUG: StatusAutomationEnum.RUNNING,
            LevelLogEnum.INFO: StatusAutomationEnum.RUNNING,
            LevelLogEnum.WARNING: StatusAutomationEnum.RUNNING,
            LevelLogEnum.ERROR: StatusAutomationEnum.FAILED,
            LevelLogEnum.CRITICAL: StatusAutomationEnum.FAILED,
        }
        status_raw = extra.pop("status", status_map[level])
        status = StatusAutomationEnum(status_raw)

        payload = self._writer.build(level, status, step, msg, **extra)
        self._writer.write(payload)
        self._writer.pretty(level, status, step, msg)
