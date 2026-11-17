"""Modelos de leitura devolvidos pelos casos de uso."""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.cliente import Cliente
from app.domain.ordem_servico import OrdemServico
from app.domain.veiculo import Veiculo


@dataclass(frozen=True)
class OrdemServicoView:
    ordem: OrdemServico
    cliente: Cliente
    veiculo: Veiculo


@dataclass(frozen=True)
class TempoMedioExecucao:
    quantidade_ordens: int
    tempo_medio_minutos: float
    tempo_medio_formatado: str
