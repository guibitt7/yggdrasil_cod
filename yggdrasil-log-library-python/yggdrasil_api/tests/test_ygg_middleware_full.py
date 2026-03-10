# tests/test_ygg_middleware_full.py
import io
import json
import uuid
import pytest
from unittest.mock import patch
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from starlette.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text

from yggdrasil_api.logger.middleware.middleware import YggApiMiddleware
from yggdrasil_api.logger.middleware.deps import get_logger, get_trace_id, get_exec_id
from yggdrasil_api.logger.middleware.logger import YggApiLogger
from yggdrasil_api.logger.middleware.metrics import RequestMetrics
from yggdrasil_api.logger.middleware.models import LevelLogEnum, StatusApiEnum
from yggdrasil_api.logger.middleware.handlers.factory import DBHandlerFactory
from yggdrasil_api.logger.middleware.handlers.base_protocol import CounterResult
from yggdrasil_api.logger.middleware.handlers.mongo import YggMongoCounter


# ─────────────────────────────────────────────
# App de teste
# ─────────────────────────────────────────────

def create_app(db=None) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        YggApiMiddleware,
        app_name="test-api",
        version="1.0.0",
        db=db,
    )

    @app.get("/ok")
    async def ok(logger: YggApiLogger = Depends(get_logger)):
        logger.info("Rota OK chamada")
        return {"status": "ok"}

    @app.get("/warn")
    async def warn(logger: YggApiLogger = Depends(get_logger)):
        logger.warning("Algo estranho aconteceu", detalhe="x")
        return {"status": "warn"}


    @app.get("/fail-4xx")
    async def fail_4xx():
        return JSONResponse(content={"error": "bad request"}, status_code=400)

    @app.get("/crash")
    async def crash():
        raise RuntimeError("Erro proposital")

    @app.get("/user")
    async def user_route(request: Request):
        request.state.logger.info("Rota com usuário autenticado", user="joao.silva")
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


@pytest.fixture
def client_no_db():
    app = create_app(db=None)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client_sqlite():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY);"))
        conn.execute(text("INSERT INTO test (id) VALUES (1);"))
    app = create_app(db=engine)
    return TestClient(app, raise_server_exceptions=False)


# ─────────────────────────────────────────────
# Helper de captura de log
# ─────────────────────────────────────────────

def _last_log(client_call_fn):
    """Intercepta stdout durante a chamada HTTP e retorna o último JSON válido."""
    buffer = io.StringIO()
    with patch("sys.stdout", buffer):
        client_call_fn()

    out = buffer.getvalue()
    json_lines = [l.strip() for l in out.split("\n") if l.strip().startswith("{")]

    if not json_lines:
        pytest.fail(f"Nenhum log JSON encontrado. Saída:\n{out}")

    return json.loads(json_lines[-1])


def _all_logs(client_call_fn):
    """Igual ao _last_log mas retorna todos os logs como lista."""
    buffer = io.StringIO()
    with patch("sys.stdout", buffer):
        client_call_fn()

    out = buffer.getvalue()
    lines = [l.strip() for l in out.split("\n") if l.strip().startswith("{")]

    if not lines:
        pytest.fail(f"Nenhum log JSON encontrado. Saída:\n{out}")

    return [json.loads(l) for l in lines]


# ─────────────────────────────────────────────
# Testes básicos de rota / middleware
# ─────────────────────────────────────────────

def test_ok_route_200(client_no_db):
    resp = client_no_db.get("/ok")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_route_ignored_trace_id(client_no_db):
    resp = client_no_db.get("/health")
    assert "x-trace-id" not in resp.headers


def test_trace_id_header_injected(client_no_db):
    resp = client_no_db.get("/ok")
    assert "x-trace-id" in resp.headers
    uuid.UUID(resp.headers["x-trace-id"])


def test_trace_id_propagated_if_valid(client_no_db):
    trace = "550e8400-e29b-41d4-a716-446655440000"
    resp = client_no_db.get("/ok", headers={"X-Trace-Id": trace})
    assert resp.headers["x-trace-id"] == trace


def test_trace_id_replaced_if_invalid(client_no_db):
    resp = client_no_db.get("/ok", headers={"X-Trace-Id": "invalid-uuid"})
    assert resp.headers["x-trace-id"] != "invalid-uuid"


# ─────────────────────────────────────────────
# Testes de logging (stdout)
# ─────────────────────────────────────────────

def test_log_ok_info_success(client_no_db):
    log = _last_log(lambda: client_no_db.get("/ok"))
    assert log["level"] == "INFO"
    assert log["status"] == "SUCCESS"


def test_warning_route_logs_success_status(client_no_db):
    log = _last_log(lambda: client_no_db.get("/warn"))
    assert log["level"] == "INFO"   # log final do middleware é INFO
    assert log["status"] == "SUCCESS"
    assert log["status_code"] == 200


def test_4xx_route_logs_failed_status(client_no_db):
    log = _last_log(lambda: client_no_db.get("/fail-4xx"))
    assert log["status"] == "FAILED"
    assert log["status_code"] == 400
    assert log["level"] == "WARNING"


def test_crash_route_logs_critical_and_exception(client_no_db):
    log = _last_log(lambda: client_no_db.get("/crash"))
    assert log["level"] == "CRITICAL"
    assert log["status"] == "FAILED"
    assert "exception" in log or "exception_class" in log
    assert "stacktrace" in log


def test_log_contains_duration_and_client_ip(client_no_db):
    log = _last_log(lambda: client_no_db.get("/ok"))
    assert isinstance(log["duration_ms"], int)
    assert "client_ip" in log


def test_user_can_be_updated_in_route(client_no_db):
    logs = _all_logs(lambda: client_no_db.get("/user"))
    assert any(l.get("user") == "joao.silva" for l in logs)


# ─────────────────────────────────────────────
# Testes de RequestMetrics
# ─────────────────────────────────────────────

def test_metrics_levels_and_status():
    m1 = RequestMetrics(start_perf=0.0, status_code=200)
    assert m1.level == LevelLogEnum.INFO
    assert m1.status == StatusApiEnum.SUCCESS

    m2 = RequestMetrics(start_perf=0.0, status_code=404)
    assert m2.level == LevelLogEnum.WARNING
    assert m2.status == StatusApiEnum.FAILED

    m3 = RequestMetrics(start_perf=0.0, status_code=500)
    assert m3.level == LevelLogEnum.CRITICAL
    assert m3.status == StatusApiEnum.FAILED


def test_metrics_build_extra_uses_dbdata():
    from starlette.requests import Request
    from starlette.datastructures import Headers
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": Headers({}).raw,
        "client": ("127.0.0.1", 12345),
    }
    req = Request(scope)
    db_data = CounterResult(count=10, failed_count=2)
    m = RequestMetrics(start_perf=0.0, status_code=200)
    extra = m.build_extra(req, db_data)
    assert extra["db_queries_count"] == 10
    assert extra["db_failed_count"] == 2


# ─────────────────────────────────────────────
# Testes de DBHandlerFactory
# ─────────────────────────────────────────────

def test_factory_with_none_does_not_break():
    app = create_app(db=None)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/ok")
    assert resp.status_code == 200


def test_factory_invalid_type_raises_type_error():
    with pytest.raises(TypeError):
        DBHandlerFactory.create("not-a-db")


def test_factory_mongo_without_counter_raises_runtimeerror():
    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017", connect=False)
    with pytest.raises(RuntimeError):
        DBHandlerFactory.create(client)


# ─────────────────────────────────────────────
# Teste de integração com SQLite + YggSQLCounter
# ─────────────────────────────────────────────

def test_sql_counter_counts_queries(client_sqlite):
    log = _last_log(lambda: client_sqlite.get("/ok"))
    assert "db_queries_count" in log
    assert isinstance(log["db_queries_count"], int)