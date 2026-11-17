import unittest

from app.infrastructure.persistence.memory import criar_uow_factory_em_memoria

from .base import ApiTestBase


class ApiComPersistenciaEmMemoriaTest(ApiTestBase, unittest.TestCase):
    def make_uow_factory(self):
        factory, _store = criar_uow_factory_em_memoria()
        return factory


if __name__ == "__main__":
    unittest.main()
