"""Persistência em memória: usada nos testes e para executar a API sem banco.

Emula as restrições do banco (unicidade e chaves estrangeiras) e a transação
(rollback restaura um snapshot do estado anterior).
"""
from __future__ import annotations

import copy
import threading
from typing import Optional

from app.application.ports import (
    ClienteRepository, OrdemServicoRepository, PecaRepository, ServicoRepository, UnitOfWork,
    VeiculoRepository,
)
from app.domain.cliente import Cliente
from app.domain.ordem_servico import OrdemServico, StatusOS
from app.domain.peca import Peca
from app.domain.servico import Servico
from app.domain.shared import ConflitoError
from app.domain.veiculo import Veiculo


class InMemoryStore:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.clientes: dict[int, Cliente] = {}
        self.veiculos: dict[int, Veiculo] = {}
        self.servicos: dict[int, Servico] = {}
        self.pecas: dict[int, Peca] = {}
        self.ordens: dict[int, OrdemServico] = {}
        self.sequencias: dict[str, int] = {}

    def proximo_id(self, nome: str) -> int:
        self.sequencias[nome] = self.sequencias.get(nome, 0) + 1
        return self.sequencias[nome]

    def snapshot(self):
        return copy.deepcopy((self.clientes, self.veiculos, self.servicos, self.pecas,
                              self.ordens, self.sequencias))

    def restaurar(self, snap) -> None:
        (self.clientes, self.veiculos, self.servicos, self.pecas, self.ordens, self.sequencias) = snap


class InMemoryClienteRepository(ClienteRepository):
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    def save(self, cliente: Cliente) -> Cliente:
        for outro in self._s.clientes.values():
            if outro.documento == cliente.documento and outro.id != cliente.id:
                raise ConflitoError("CPF/CNPJ já cadastrado")
        if cliente.id is None:
            cliente.id = self._s.proximo_id("cliente")
        self._s.clientes[cliente.id] = cliente
        return cliente

    def get(self, id: int) -> Optional[Cliente]:
        return self._s.clientes.get(id)

    def get_by_documento(self, numero: str) -> Optional[Cliente]:
        return next((c for c in self._s.clientes.values() if c.documento.numero == numero), None)

    def list_all(self) -> list[Cliente]:
        return list(self._s.clientes.values())

    def delete(self, id: int) -> None:
        if any(v.cliente_id == id for v in self._s.veiculos.values()) or \
                any(o.cliente_id == id for o in self._s.ordens.values()):
            raise ConflitoError("Cliente possui veículos ou ordens de serviço vinculados")
        self._s.clientes.pop(id, None)


class InMemoryVeiculoRepository(VeiculoRepository):
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    def save(self, veiculo: Veiculo) -> Veiculo:
        for outro in self._s.veiculos.values():
            if outro.placa == veiculo.placa and outro.id != veiculo.id:
                raise ConflitoError("Placa já cadastrada")
        if veiculo.id is None:
            veiculo.id = self._s.proximo_id("veiculo")
        self._s.veiculos[veiculo.id] = veiculo
        return veiculo

    def get(self, id: int) -> Optional[Veiculo]:
        return self._s.veiculos.get(id)

    def get_by_placa(self, numero: str) -> Optional[Veiculo]:
        return next((v for v in self._s.veiculos.values() if v.placa.numero == numero), None)

    def list_all(self, cliente_id: Optional[int] = None) -> list[Veiculo]:
        return [v for v in self._s.veiculos.values() if cliente_id is None or v.cliente_id == cliente_id]

    def delete(self, id: int) -> None:
        if any(o.veiculo_id == id for o in self._s.ordens.values()):
            raise ConflitoError("Veículo possui ordens de serviço vinculadas")
        self._s.veiculos.pop(id, None)


class InMemoryServicoRepository(ServicoRepository):
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    def save(self, servico: Servico) -> Servico:
        if servico.id is None:
            servico.id = self._s.proximo_id("servico")
        self._s.servicos[servico.id] = servico
        return servico

    def get(self, id: int) -> Optional[Servico]:
        return self._s.servicos.get(id)

    def list_all(self) -> list[Servico]:
        return list(self._s.servicos.values())

    def delete(self, id: int) -> None:
        if any(i.servico_id == id for o in self._s.ordens.values() for i in o.servicos):
            raise ConflitoError("Serviço está em uso em ordens de serviço")
        self._s.servicos.pop(id, None)


class InMemoryPecaRepository(PecaRepository):
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    def save(self, peca: Peca) -> Peca:
        for outra in self._s.pecas.values():
            if outra.codigo == peca.codigo and outra.id != peca.id:
                raise ConflitoError("Código de peça já cadastrado")
        if peca.id is None:
            peca.id = self._s.proximo_id("peca")
        self._s.pecas[peca.id] = peca
        return peca

    def get(self, id: int) -> Optional[Peca]:
        return self._s.pecas.get(id)

    def get_by_codigo(self, codigo: str) -> Optional[Peca]:
        return next((p for p in self._s.pecas.values() if p.codigo == codigo), None)

    def list_all(self) -> list[Peca]:
        return list(self._s.pecas.values())

    def delete(self, id: int) -> None:
        if any(i.peca_id == id for o in self._s.ordens.values() for i in o.pecas):
            raise ConflitoError("Peça está em uso em ordens de serviço")
        self._s.pecas.pop(id, None)


class InMemoryOrdemServicoRepository(OrdemServicoRepository):
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    def save(self, ordem: OrdemServico) -> OrdemServico:
        if ordem.id is None:
            ordem.id = self._s.proximo_id("ordem")
        self._s.ordens[ordem.id] = ordem
        return ordem

    def get(self, id: int) -> Optional[OrdemServico]:
        return self._s.ordens.get(id)

    def get_by_codigo(self, codigo: str) -> Optional[OrdemServico]:
        return next((o for o in self._s.ordens.values() if o.codigo_acompanhamento == codigo), None)

    def list_all(self, status: Optional[StatusOS] = None) -> list[OrdemServico]:
        ordens = [o for o in self._s.ordens.values() if status is None or o.status == status]
        return sorted(ordens, key=lambda o: (o.criada_em, o.id))

    def list_executadas(self) -> list[OrdemServico]:
        return [o for o in self._s.ordens.values()
                if o.inicio_execucao_em is not None and o.fim_execucao_em is not None]


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store
        self._snapshot = None

    def __enter__(self) -> "InMemoryUnitOfWork":
        self._store.lock.acquire()
        self._snapshot = self._store.snapshot()
        self.clientes = InMemoryClienteRepository(self._store)
        self.veiculos = InMemoryVeiculoRepository(self._store)
        self.servicos = InMemoryServicoRepository(self._store)
        self.pecas = InMemoryPecaRepository(self._store)
        self.ordens = InMemoryOrdemServicoRepository(self._store)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is not None:
                self._store.restaurar(self._snapshot)
        finally:
            self._snapshot = None
            self._store.lock.release()


def criar_uow_factory_em_memoria():
    """Retorna (factory, store) — o store permite inspeção nos testes."""
    store = InMemoryStore()
    return (lambda: InMemoryUnitOfWork(store)), store
