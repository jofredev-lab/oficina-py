"""Agregado Serviço do catálogo da oficina."""
from __future__ import annotations

from decimal import Decimal

from .shared import RegraNegocioError, quantizar


class Servico:
    def __init__(self, nome: str, descricao: str | None, preco: Decimal | int | float | str,
                 id: int | None = None) -> None:
        self.id = id
        self._preencher(nome, descricao, preco)

    def atualizar(self, nome: str, descricao: str | None, preco) -> None:
        self._preencher(nome, descricao, preco)

    def _preencher(self, nome, descricao, preco) -> None:
        if nome is None or not str(nome).strip():
            raise RegraNegocioError("Nome do serviço é obrigatório")
        if preco is None or quantizar(preco) < 0:
            raise RegraNegocioError("Preço do serviço não pode ser negativo")
        self.nome = str(nome).strip()
        self.descricao = descricao
        self.preco = quantizar(preco)
