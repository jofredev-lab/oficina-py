"""Dados de entrada dos casos de uso (independentes de HTTP)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ClienteDados:
    nome: str
    documento: str
    email: str | None = None
    telefone: str | None = None


@dataclass(frozen=True)
class VeiculoDados:
    placa: str
    marca: str
    modelo: str
    ano: int
    cliente_id: int


@dataclass(frozen=True)
class VeiculoOSDados:
    """Veículo informado na abertura da OS (cadastrado se a placa ainda não existir)."""

    placa: str
    marca: str
    modelo: str
    ano: int


@dataclass(frozen=True)
class ServicoDados:
    nome: str
    descricao: str | None
    preco: Decimal


@dataclass(frozen=True)
class PecaDados:
    codigo: str
    nome: str
    preco: Decimal
    quantidade_estoque: int
    estoque_minimo: int


@dataclass(frozen=True)
class ItemPecaDados:
    peca_id: int
    quantidade: int


@dataclass(frozen=True)
class ItensDados:
    servicos_ids: tuple[int, ...] = ()
    pecas: tuple[ItemPecaDados, ...] = ()


@dataclass(frozen=True)
class AbrirOrdemServicoDados:
    documento_cliente: str
    veiculo: VeiculoOSDados
    itens: ItensDados = ItensDados()
