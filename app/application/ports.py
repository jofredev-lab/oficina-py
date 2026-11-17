"""Portas (contratos) de persistência e unidade de trabalho.

O domínio e os casos de uso dependem apenas destas abstrações; as implementações
ficam em ``app.infrastructure.persistence`` (SQLAlchemy/PostgreSQL e em memória).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.cliente import Cliente
from app.domain.ordem_servico import OrdemServico, StatusOS
from app.domain.peca import Peca
from app.domain.servico import Servico
from app.domain.veiculo import Veiculo


class ClienteRepository(ABC):
    @abstractmethod
    def save(self, cliente: Cliente) -> Cliente: ...

    @abstractmethod
    def get(self, id: int) -> Optional[Cliente]: ...

    @abstractmethod
    def get_by_documento(self, numero: str) -> Optional[Cliente]: ...

    @abstractmethod
    def list_all(self) -> list[Cliente]: ...

    @abstractmethod
    def delete(self, id: int) -> None: ...


class VeiculoRepository(ABC):
    @abstractmethod
    def save(self, veiculo: Veiculo) -> Veiculo: ...

    @abstractmethod
    def get(self, id: int) -> Optional[Veiculo]: ...

    @abstractmethod
    def get_by_placa(self, numero: str) -> Optional[Veiculo]: ...

    @abstractmethod
    def list_all(self, cliente_id: Optional[int] = None) -> list[Veiculo]: ...

    @abstractmethod
    def delete(self, id: int) -> None: ...


class ServicoRepository(ABC):
    @abstractmethod
    def save(self, servico: Servico) -> Servico: ...

    @abstractmethod
    def get(self, id: int) -> Optional[Servico]: ...

    @abstractmethod
    def list_all(self) -> list[Servico]: ...

    @abstractmethod
    def delete(self, id: int) -> None: ...


class PecaRepository(ABC):
    @abstractmethod
    def save(self, peca: Peca) -> Peca: ...

    @abstractmethod
    def get(self, id: int) -> Optional[Peca]: ...

    @abstractmethod
    def get_by_codigo(self, codigo: str) -> Optional[Peca]: ...

    @abstractmethod
    def list_all(self) -> list[Peca]: ...

    @abstractmethod
    def delete(self, id: int) -> None: ...


class OrdemServicoRepository(ABC):
    @abstractmethod
    def save(self, ordem: OrdemServico) -> OrdemServico: ...

    @abstractmethod
    def get(self, id: int) -> Optional[OrdemServico]: ...

    @abstractmethod
    def get_by_codigo(self, codigo: str) -> Optional[OrdemServico]: ...

    @abstractmethod
    def list_all(self, status: Optional[StatusOS] = None) -> list[OrdemServico]:
        """Fila de atendimento: mais antigas primeiro (FIFO)."""

    @abstractmethod
    def list_executadas(self) -> list[OrdemServico]:
        """OS que passaram por execução (têm início e fim de execução)."""


class UnitOfWork(ABC):
    """Unidade de trabalho = uma transação. Sai do ``with`` com erro => rollback; sem erro => commit."""

    clientes: ClienteRepository
    veiculos: VeiculoRepository
    servicos: ServicoRepository
    pecas: PecaRepository
    ordens: OrdemServicoRepository

    @abstractmethod
    def __enter__(self) -> "UnitOfWork": ...

    @abstractmethod
    def __exit__(self, exc_type, exc, tb) -> None: ...
