"""Agregado Peça/Insumo com controle de estoque."""
from __future__ import annotations

from .shared import RegraNegocioError, quantizar


def _inteiro_nao_negativo(valor) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool) and valor >= 0


class Peca:
    def __init__(self, codigo: str, nome: str, preco, quantidade_estoque: int, estoque_minimo: int,
                 id: int | None = None) -> None:
        self.id = id
        self._preencher(codigo, nome, preco, quantidade_estoque, estoque_minimo)

    def atualizar(self, codigo: str, nome: str, preco, quantidade_estoque: int, estoque_minimo: int) -> None:
        self._preencher(codigo, nome, preco, quantidade_estoque, estoque_minimo)

    def _preencher(self, codigo, nome, preco, quantidade_estoque, estoque_minimo) -> None:
        if codigo is None or not str(codigo).strip():
            raise RegraNegocioError("Código da peça é obrigatório")
        if nome is None or not str(nome).strip():
            raise RegraNegocioError("Nome da peça é obrigatório")
        if preco is None or quantizar(preco) < 0:
            raise RegraNegocioError("Preço da peça não pode ser negativo")
        if not _inteiro_nao_negativo(quantidade_estoque) or not _inteiro_nao_negativo(estoque_minimo):
            raise RegraNegocioError("Estoque não pode ser negativo")
        self.codigo = str(codigo).strip().upper()
        self.nome = str(nome).strip()
        self.preco = quantizar(preco)
        self.quantidade_estoque = quantidade_estoque
        self.estoque_minimo = estoque_minimo

    def baixar_estoque(self, quantidade: int) -> None:
        self._validar_quantidade(quantidade)
        if quantidade > self.quantidade_estoque:
            raise RegraNegocioError(
                f"Estoque insuficiente da peça {self.codigo}: "
                f"disponível {self.quantidade_estoque}, solicitado {quantidade}")
        self.quantidade_estoque -= quantidade

    def repor_estoque(self, quantidade: int) -> None:
        self._validar_quantidade(quantidade)
        self.quantidade_estoque += quantidade

    @property
    def estoque_baixo(self) -> bool:
        return self.quantidade_estoque <= self.estoque_minimo

    @staticmethod
    def _validar_quantidade(quantidade) -> None:
        if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade <= 0:
            raise RegraNegocioError("Quantidade deve ser maior que zero")
