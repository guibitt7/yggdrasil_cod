import threading
from pymongo.monitoring import CommandListener
from yggdrasil_api.logger.middleware.handlers.base_protocol import (
    YggDBHandler,
    CounterResult,
)


_IGNORED_COMMANDS = {
    "hello",
    "ping",
    "endSessions",
    "isMaster",
    "buildInfo",
    "getLastError",
    "listCollections",
    "listDatabases",
    "serverStatus",
    "connectionStatus",
}


class YggMongoCounter(CommandListener, YggDBHandler):
    def __init__(self):
        self._count = 0
        self._failed_count = 0
        self._lock = threading.Lock()

    def started(self, event) -> None:
        if event.command_name not in _IGNORED_COMMANDS:
            with self._lock:
                self._count += 1

    def succeeded(self, event) -> None:
        pass

    def failed(self, event) -> None:
        if event.command_name not in _IGNORED_COMMANDS:
            with self._lock:
                self._failed_count += 1

    def reset(self) -> CounterResult:
        with self._lock:
            count = self._count
            failed = self._failed_count
            self._count = 0
            self._failed_count = 0
            return CounterResult(count=count, failed_count=failed)

    @property
    def count(self) -> int:
        with self._lock:
            return self._count

    @property
    def failed_count(self) -> int:
        with self._lock:
            return self._failed_count
