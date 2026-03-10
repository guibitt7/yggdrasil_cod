import threading
from sqlalchemy import event
from sqlalchemy.engine import Engine
from yggdrasil_api.logger.middleware.handlers.base_protocol import (
    YggDBHandler,
    CounterResult,
)


class YggSQLCounter(YggDBHandler):
    def __init__(self):
        self._count = 0
        self._lock = threading.Lock()

    def attach(self, engine: Engine) -> None:
        """Registra o listener no engine do SQLAlchemy."""
        if not event.contains(
            engine, "before_cursor_execute", self._before_cursor_execute
        ):
            event.listen(engine, "before_cursor_execute", self._before_cursor_execute)

    def detach(self, engine: Engine) -> None:
        """Remove o listener do engine."""
        if event.contains(engine, "before_cursor_execute", self._before_cursor_execute):
            event.remove(engine, "before_cursor_execute", self._before_cursor_execute)

    def _before_cursor_execute(
        self, conn, cursor, statement, parameters, context, executemany
    ) -> None:
        with self._lock:
            self._count += 1

    def reset(self) -> CounterResult:
        with self._lock:
            count = self._count
            self._count = 0
            return CounterResult(count=count)

    @property
    def count(self) -> int:
        with self._lock:
            return self._count
