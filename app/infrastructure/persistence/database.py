"""Criação do engine/sessões SQLAlchemy e do schema (MVP: create_all; próxima fase: Alembic)."""
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base
from .sqlalchemy_repositories import SqlAlchemyUnitOfWork


def criar_engine(database_url: str):
    if database_url.startswith("sqlite"):
        engine = create_engine(database_url, poolclass=StaticPool, connect_args={"check_same_thread": False})

        @event.listens_for(engine, "connect")
        def _ativar_chaves_estrangeiras(dbapi_connection, _record):  # pragma: no cover
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine
    return create_engine(database_url, pool_pre_ping=True)


def criar_uow_factory(database_url: str, criar_schema: bool = True):
    engine = criar_engine(database_url)
    if criar_schema:
        Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return lambda: SqlAlchemyUnitOfWork(session_factory)
