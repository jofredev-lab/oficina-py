"""Tratamento global de erros no formato Problem Details (RFC 7807)."""
from __future__ import annotations

import logging
from http import HTTPStatus

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.domain.shared import ConflitoError, RecursoNaoEncontradoError, RegraNegocioError
from app.infrastructure.security.jwt_service import CredenciaisInvalidasError, NaoAutenticadoError

from .validation import ValidationError

log = logging.getLogger(__name__)


def problem(status: int, detail: str, **extras):
    corpo = {"type": "about:blank", "title": HTTPStatus(status).phrase, "status": status,
             "detail": detail, **extras}
    resposta = jsonify(corpo)
    resposta.status_code = status
    resposta.mimetype = "application/problem+json"
    return resposta


def registrar_tratadores_de_erro(app: Flask) -> None:
    @app.errorhandler(RecursoNaoEncontradoError)
    def _nao_encontrado(e):
        return problem(404, str(e))

    @app.errorhandler(RegraNegocioError)
    def _regra_negocio(e):
        return problem(422, str(e))

    @app.errorhandler(ConflitoError)
    def _conflito(e):
        return problem(409, str(e))

    @app.errorhandler(ValidationError)
    def _validacao(e):
        return problem(400, "Dados inválidos", erros=e.erros)

    @app.errorhandler(CredenciaisInvalidasError)
    def _credenciais(e):
        return problem(401, str(e))

    @app.errorhandler(NaoAutenticadoError)
    def _nao_autenticado(e):
        return problem(401, str(e))

    @app.errorhandler(HTTPException)
    def _http(e):
        return problem(e.code or 500, e.description or HTTPStatus(e.code or 500).phrase)

    @app.errorhandler(Exception)
    def _inesperado(e):  # pragma: no cover - rede de segurança
        log.exception("Erro inesperado")
        return problem(500, "Erro interno do servidor")
