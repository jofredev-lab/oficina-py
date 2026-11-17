"""Agregado Veículo e objeto de valor Placa."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from .shared import RegraNegocioError

_PADRAO_PLACA = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")


@dataclass(frozen=True)
class Placa:
    """Objeto de valor: placa no padrão antigo (ABC1234) ou Mercosul (ABC1D23)."""

    numero: str

    def __post_init__(self) -> None:
        if not _PADRAO_PLACA.match(self.numero):
            raise RegraNegocioError("Placa inválida: use o formato ABC1234 ou ABC1D23")

    @classmethod
    def of(cls, valor: str | None) -> "Placa":
        if valor is None or not str(valor).strip():
            raise RegraNegocioError("Placa é obrigatória")
        return cls(re.sub(r"[\s-]", "", str(valor)).upper())

    def __str__(self) -> str:
        return self.numero


class Veiculo:
    """Agregado Veículo, sempre vinculado a um cliente (referenciado por id)."""

    def __init__(self, placa: Placa, marca: str, modelo: str, ano: int, cliente_id: int,
                 id: int | None = None) -> None:
        self.id = id
        self._preencher(placa, marca, modelo, ano, cliente_id)

    def atualizar(self, placa: Placa, marca: str, modelo: str, ano: int, cliente_id: int) -> None:
        self._preencher(placa, marca, modelo, ano, cliente_id)

    def _preencher(self, placa, marca, modelo, ano, cliente_id) -> None:
        if placa is None:
            raise RegraNegocioError("Placa é obrigatória")
        if marca is None or not str(marca).strip():
            raise RegraNegocioError("Marca do veículo é obrigatória")
        if modelo is None or not str(modelo).strip():
            raise RegraNegocioError("Modelo do veículo é obrigatório")
        if not isinstance(ano, int) or isinstance(ano, bool) or ano < 1900 or ano > date.today().year + 1:
            raise RegraNegocioError("Ano do veículo inválido")
        if cliente_id is None:
            raise RegraNegocioError("Veículo deve pertencer a um cliente")
        self.placa = placa
        self.marca = str(marca).strip()
        self.modelo = str(modelo).strip()
        self.ano = ano
        self.cliente_id = cliente_id
