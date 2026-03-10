# main.py
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from yggdrasil_api.logger.middleware import (
    YggApiMiddleware,
    YggApiLogger,
    get_logger,
    get_trace_id,
)

app = FastAPI()

# SQL
engine = create_engine("postgresql+psycopg2://user:pass@localhost/db")
app.add_middleware(YggApiMiddleware, app_name="api-vendas", version="1.2.0", db=engine)

# Mongo
# counter = YggMongoCounter()
# client = MongoClient("mongodb://localhost:27017", event_listeners=[counter])
# app.add_middleware(YggApiMiddleware, app_name="api-docs", version="1.0.0", db=client)


@app.get("/vendas")
async def get_vendas(logger: YggApiLogger = Depends(get_logger)):
    logger.info("Buscando vendas no banco...")
    return {"data": [1, 2, 3]}


@app.get("/vendas/{id}")
async def get_venda_by_id(id: int, logger: YggApiLogger = Depends(get_logger)):
    if id <= 0:
        logger.warning("ID inválido recebido", id=id)
        return {"error": "ID inválido"}, 400
    logger.info("Venda encontrada", venda_id=id)
    return {"id": id, "valor": 100.0}


@app.get("/crash")
async def crash():
    raise RuntimeError("Erro proposital para testar o middleware")