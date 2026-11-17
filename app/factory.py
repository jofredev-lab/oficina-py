"""Fábrica da aplicação Flask (raiz de composição)."""
from __future__ import annotations

from typing import Callable

from flask import Flask

from app.application.cadastros import ClienteService, PecaService, ServicoService, VeiculoService
from app.application.ordens import OrdemServicoService
from app.application.ports import UnitOfWork
from app.config import Settings
from app.container import Container
from app.infrastructure.security.jwt_service import AuthService, JwtService
from app.interfaces.api import acompanhamento, auth, clientes, docs, metricas, ordens, pecas, servicos, veiculos
from app.interfaces.errors import registrar_tratadores_de_erro


def create_app(settings: Settings | None = None,
               uow_factory: Callable[[], UnitOfWork] | None = None) -> Flask:
    """Cria a aplicação.

    ``uow_factory`` permite injetar a persistência (os testes usam a implementação em memória);
    sem ele, usa PostgreSQL via SQLAlchemy conforme ``settings.database_url``.
    """
    settings = settings or Settings.from_env()

    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.json.sort_keys = False
    app.url_map.strict_slashes = False

    if uow_factory is None:
        from app.infrastructure.persistence.database import criar_uow_factory
        uow_factory = criar_uow_factory(settings.database_url)

    jwt_service = JwtService(settings.jwt_secret, settings.jwt_expiration_seconds)
    app.extensions["oficina"] = Container(
        clientes=ClienteService(uow_factory),
        veiculos=VeiculoService(uow_factory),
        servicos=ServicoService(uow_factory),
        pecas=PecaService(uow_factory),
        ordens=OrdemServicoService(uow_factory),
        jwt=jwt_service,
        auth=AuthService(jwt_service, settings.admin_username, settings.admin_password),
    )

    registrar_tratadores_de_erro(app)
    for modulo in (auth, clientes, veiculos, servicos, pecas, ordens, acompanhamento, metricas, docs):
        app.register_blueprint(modulo.bp)
    return app
