from os import makedirs, path
from json import dumps
from platform import system
from datetime import datetime, timezone
from yggdrasil.logger.models import (
    ParamsLogger,
    Colors,
    LevelLogEnum,
    StatusAutomationEnum,
)
from yggdrasil.environment.settings import ROBOT


class LogWriter:
    def __init__(self, params_logger: ParamsLogger, start_time: str):
        self._params = params_logger
        self.start_time = start_time

        log_dir = self.define_log_dir()
        
        makedirs(log_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.log_file = path.join(log_dir, f"{ROBOT}_{date_str}.log")

    def build(
        self,
        level: LevelLogEnum,
        status: StatusAutomationEnum,
        step: str,
        msg: str,
        **kwargs,
    ) -> str:
        """Monta o JSON do log."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "automacao": self._params.automation_name,
            "robot": ROBOT,
            "usuario_impessoal": self._params.impersonal_user,
            "exec_id": str(self._params.exec_id),
            "trace_id": str(self._params.trace_id),
            "fluid_id": self._params.fluid_id,
            "status": status,
            "step": step,
            "start_time": self.start_time,
            "msg": msg,
        }
        entry.update(kwargs)
        return dumps(entry, ensure_ascii=False)

    def write(self, payload: str):
        """Escreve no arquivo de log. Se falhar, não derruba a automação."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as file:
                file.write(payload + "\n")
        except Exception as e:
            print(f"[ERRO YGG_LOGGER] Falha ao escrever no arquivo: {e}")

    def pretty(
        self, level: LevelLogEnum, status: StatusAutomationEnum, step: str, msg: str
    ):
        """Exibe o log colorido no terminal."""
        color = getattr(Colors, level.name, Colors.RESET)
        now = datetime.now().strftime("%H:%M:%S")
        print(
            f"[{now}] {color}| {level.value:<8} |{Colors.RESET} | {status.value:<8} | {Colors.STEP}{step:<30}{Colors.RESET} | {msg}"
        )
    
    @staticmethod
    def define_log_dir():
        if system() == "Windows":
            return r"C:\ProgramData\Yggdrasil\Logs"
        return path.expanduser("~/Documents/Yggdrasil/Logs")