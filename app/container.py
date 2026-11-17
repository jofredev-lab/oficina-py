"""Raiz de composição: agrupa os serviços usados pelas rotas."""
from __future__ import annotations

from dataclasses import dataclass

from app.application.cadastros import ClienteService, PecaService, ServicoService, VeiculoService
from app.application.ordens import OrdemServicoService
from app.infrastructure.security.jwt_service import AuthService, JwtService


@dataclass(frozen=True)
class Container:
    clientes: ClienteService
    veiculos: VeiculoService
    servicos: ServicoService
    pecas: PecaService
    ordens: OrdemServicoService
    jwt: JwtService
    auth: AuthService
