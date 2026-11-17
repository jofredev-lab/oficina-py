"""Mesma suíte da API, agora contra SQLAlchemy (SQLite em memória) — mesmo código usado com PostgreSQL."""
import unittest

try:
    import sqlalchemy  # noqa: F401
    HAS_SQLALCHEMY = True
except ImportError:  # pragma: no cover
    HAS_SQLALCHEMY = False

from .base import ApiTestBase


@unittest.skipUnless(HAS_SQLALCHEMY, "SQLAlchemy não instalado (pip install -r requirements.txt)")
class ApiComSqlAlchemyTest(ApiTestBase, unittest.TestCase):
    def make_uow_factory(self):
        from app.infrastructure.persistence.database import criar_uow_factory
        return criar_uow_factory("sqlite+pysqlite:///:memory:")


if __name__ == "__main__":
    unittest.main()
