import unittest

from app.domain.cliente import Cliente, Documento
from app.domain.shared import ConflitoError
from app.infrastructure.persistence.memory import criar_uow_factory_em_memoria


class UnitOfWorkEmMemoriaTest(unittest.TestCase):
    def test_commit_persiste_e_rollback_desfaz(self):
        factory, store = criar_uow_factory_em_memoria()
        with factory() as uow:
            uow.clientes.save(Cliente("Ana", Documento.of("529.982.247-25")))
        self.assertEqual(1, len(store.clientes))

        with self.assertRaises(RuntimeError):
            with factory() as uow:
                uow.clientes.save(Cliente("Beto", Documento.of("111.444.777-35")))
                raise RuntimeError("falha no meio da transação")
        self.assertEqual(1, len(store.clientes))

    def test_unicidade_de_documento(self):
        factory, _ = criar_uow_factory_em_memoria()
        with factory() as uow:
            uow.clientes.save(Cliente("Ana", Documento.of("529.982.247-25")))
            with self.assertRaises(ConflitoError):
                uow.clientes.save(Cliente("Outra", Documento.of("529.982.247-25")))


if __name__ == "__main__":
    unittest.main()
