"""Configuração da aplicação via variáveis de ambiente (com valores de demonstração)."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = "postgresql+psycopg2://oficina:oficina@localhost:5432/oficina"
    jwt_secret: str = "demo-secret-key-troque-em-producao-0123456789"
    jwt_expiration_seconds: int = 3600
    admin_username: str = "admin"
    admin_password: str = "admin123"

    @classmethod
    def from_env(cls) -> "Settings":
        padrao = cls()
        return cls(
            database_url=os.getenv("DATABASE_URL", padrao.database_url),
            jwt_secret=os.getenv("JWT_SECRET", padrao.jwt_secret),
            jwt_expiration_seconds=int(os.getenv("JWT_EXPIRATION_SECONDS", padrao.jwt_expiration_seconds)),
            admin_username=os.getenv("ADMIN_USERNAME", padrao.admin_username),
            admin_password=os.getenv("ADMIN_PASSWORD", padrao.admin_password),
        )
