# yggdrasil/logger/middleware/handlers/factory.py
from sqlalchemy.engine import Engine
from pymongo import MongoClient
from yggdrasil_api.logger.middleware.handlers.sql import YggSQLCounter
from yggdrasil_api.logger.middleware.handlers.mongo import YggMongoCounter
from yggdrasil_api.logger.middleware.handlers.base_protocol import YggDBHandler


class DBHandlerFactory:
    @staticmethod
    def create(db_instance) -> YggDBHandler:
        if isinstance(db_instance, Engine):
            return DBHandlerFactory._create_sql_handler(db_instance)

        if isinstance(db_instance, MongoClient):
            return DBHandlerFactory._create_mongo_handler(db_instance)

        raise TypeError(
            f"Banco não suportado: {type(db_instance).__name__}. "
            "Esperado: Engine (SQLAlchemy) ou MongoClient (pymongo)."
        )

    @staticmethod
    def _create_sql_handler(engine: Engine) -> YggSQLCounter:
        handler = YggSQLCounter()
        handler.attach(engine)
        return handler

    @staticmethod
    def _create_mongo_handler(mongo_client: MongoClient) -> YggMongoCounter:
        listeners_obj = getattr(mongo_client, "_event_listeners", None)
        command_listeners = getattr(listeners_obj, "command_listeners", [])

        mongo_counter = next(
            (l for l in command_listeners if isinstance(l, YggMongoCounter)),
            None,
        )

        if mongo_counter is None:
            raise RuntimeError(
                "YggMongoCounter não encontrado nos event_listeners do MongoClient. "
                "Inicialize o client corretamente:\n\n"
                "    counter = YggMongoCounter()\n"
                "    client = MongoClient(..., event_listeners=[counter])"
            )

        return mongo_counter
