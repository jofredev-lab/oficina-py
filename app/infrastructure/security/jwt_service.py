"""Emissão/validação de tokens JWT (HS256) e autenticação do administrador."""
from __future__ import annotations

import hmac
from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.security import check_password_hash, generate_password_hash


class CredenciaisInvalidasError(Exception):
    """Usuário ou senha inválidos (HTTP 401)."""

    def __init__(self) -> None:
        super().__init__("Usuário ou senha inválidos")


class NaoAutenticadoError(Exception):
    """Token ausente, inválido ou expirado (HTTP 401)."""

    def __init__(self) -> None:
        super().__init__("Não autenticado: informe um token JWT válido")


class JwtService:
    ALGORITMO = "HS256"

    def __init__(self, secret: str, expiracao_segundos: int) -> None:
        if len(secret.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET deve ter ao menos 32 caracteres")
        self._secret = secret
        self.expiracao_segundos = expiracao_segundos

    def gerar(self, usuario: str) -> str:
        agora = datetime.now(timezone.utc)
        claims = {"sub": usuario, "iat": agora, "exp": agora + timedelta(seconds=self.expiracao_segundos)}
        return jwt.encode(claims, self._secret, algorithm=self.ALGORITMO)

    def validar(self, token: str) -> dict:
        """Lança ``jwt.InvalidTokenError`` se o token for inválido ou estiver expirado."""
        return jwt.decode(token, self._secret, algorithms=[self.ALGORITMO],
                          options={"require": ["exp", "sub"]})


class AuthService:
    """Autentica o usuário administrador (credenciais vindas de configuração/ambiente)."""

    def __init__(self, jwt_service: JwtService, usuario_admin: str, senha_admin: str) -> None:
        self._jwt = jwt_service
        self._usuario = usuario_admin
        self._senha_hash = generate_password_hash(senha_admin)

    def autenticar(self, username: str, password: str) -> tuple[str, int]:
        usuario_ok = hmac.compare_digest(username.encode("utf-8"), self._usuario.encode("utf-8"))
        senha_ok = check_password_hash(self._senha_hash, password)
        if not (usuario_ok and senha_ok):
            raise CredenciaisInvalidasError()
        return self._jwt.gerar(self._usuario), self._jwt.expiracao_segundos
