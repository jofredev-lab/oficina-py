"""Exceções de negócio e utilidades comuns do domínio."""
from decimal import ROUND_HALF_UP, Decimal


class DomainError(Exception):
    """Base das exceções do domínio."""


class RegraNegocioError(DomainError):
    """Violação de uma regra de negócio (HTTP 422)."""


class RecursoNaoEncontradoError(DomainError):
    """Agregado/entidade não encontrado (HTTP 404)."""


class ConflitoError(DomainError):
    """Conflito com o estado atual: duplicidade ou registro em uso (HTTP 409)."""


def quantizar(valor) -> Decimal:
    """Converte para Decimal com 2 casas (arredondamento comercial)."""
    if not isinstance(valor, Decimal):
        valor = Decimal(str(valor))
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
