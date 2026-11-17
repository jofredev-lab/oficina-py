"""Agregado Cliente e objeto de valor Documento (CPF/CNPJ)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .shared import RegraNegocioError

_PESOS_CNPJ_1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_PESOS_CNPJ_2 = (6,) + _PESOS_CNPJ_1


class TipoDocumento(str, Enum):
    CPF = "CPF"
    CNPJ = "CNPJ"


@dataclass(frozen=True)
class Documento:
    """Objeto de valor: CPF ou CNPJ válido, guardado somente com dígitos."""

    numero: str

    def __post_init__(self) -> None:
        digitos = self.numero
        if not re.fullmatch(r"[0-9]*", digitos):
            raise RegraNegocioError("CPF/CNPJ deve conter apenas dígitos")
        if len(digitos) == 11:
            if not _cpf_valido(digitos):
                raise RegraNegocioError("CPF inválido")
        elif len(digitos) == 14:
            if not _cnpj_valido(digitos):
                raise RegraNegocioError("CNPJ inválido")
        else:
            raise RegraNegocioError("CPF/CNPJ deve conter 11 (CPF) ou 14 (CNPJ) dígitos")

    @classmethod
    def of(cls, valor: str | None) -> "Documento":
        if valor is None or not str(valor).strip():
            raise RegraNegocioError("CPF/CNPJ é obrigatório")
        return cls(re.sub(r"[^0-9]", "", str(valor)))

    @property
    def tipo(self) -> TipoDocumento:
        return TipoDocumento.CPF if len(self.numero) == 11 else TipoDocumento.CNPJ

    def __str__(self) -> str:
        return self.numero


def _todos_iguais(c: str) -> bool:
    return len(set(c)) == 1


def _digito_cpf(c: str, tamanho: int, peso_inicial: int) -> int:
    soma = sum(int(c[i]) * (peso_inicial - i) for i in range(tamanho))
    resto = (soma * 10) % 11
    return 0 if resto == 10 else resto


def _cpf_valido(c: str) -> bool:
    if _todos_iguais(c):
        return False
    return _digito_cpf(c, 9, 10) == int(c[9]) and _digito_cpf(c, 10, 11) == int(c[10])


def _digito_cnpj(c: str, pesos: tuple[int, ...]) -> int:
    soma = sum(int(c[i]) * pesos[i] for i in range(len(pesos)))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def _cnpj_valido(c: str) -> bool:
    if _todos_iguais(c):
        return False
    return _digito_cnpj(c, _PESOS_CNPJ_1) == int(c[12]) and _digito_cnpj(c, _PESOS_CNPJ_2) == int(c[13])


class Cliente:
    """Agregado Cliente, identificado de forma única por CPF/CNPJ."""

    def __init__(self, nome: str, documento: Documento, email: str | None = None,
                 telefone: str | None = None, id: int | None = None) -> None:
        self.id = id
        self._preencher(nome, documento, email, telefone)

    def atualizar(self, nome: str, documento: Documento, email: str | None = None,
                  telefone: str | None = None) -> None:
        self._preencher(nome, documento, email, telefone)

    def _preencher(self, nome, documento, email, telefone) -> None:
        if nome is None or not str(nome).strip():
            raise RegraNegocioError("Nome do cliente é obrigatório")
        if documento is None:
            raise RegraNegocioError("CPF/CNPJ do cliente é obrigatório")
        self.nome = str(nome).strip()
        self.documento = documento
        self.email = email
        self.telefone = telefone
