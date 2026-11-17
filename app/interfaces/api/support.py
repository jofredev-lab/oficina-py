"""Infraestrutura das rotas: decorador ``endpoint`` (autenticação + resposta JSON + registro para o OpenAPI)."""
from __future__ import annotations

import functools
from dataclasses import dataclass

import jwt
from flask import Blueprint, current_app, g, jsonify, request

from app.container import Container
from app.infrastructure.security.jwt_service import NaoAutenticadoError


@dataclass(frozen=True)
class OperacaoDoc:
    regra: str
    metodo: str
    resumo: str
    tag: str
    requisicao: str | None
    status: int
    resposta: str | None
    protegida: bool
    consulta: tuple


REGISTRO: list[OperacaoDoc] = []


def container() -> Container:
    return current_app.extensions["oficina"]


def exigir_admin() -> None:
    cabecalho = request.headers.get("Authorization", "")
    if not cabecalho.startswith("Bearer "):
        raise NaoAutenticadoError()
    try:
        claims = container().jwt.validar(cabecalho[len("Bearer "):])
    except jwt.InvalidTokenError:
        raise NaoAutenticadoError() from None
    g.usuario = claims["sub"]


def endpoint(bp: Blueprint, regra: str, metodo: str, *, resumo: str, tag: str, status: int = 200,
             requisicao: str | None = None, resposta: str | None = None, protegida: bool = True,
             consulta: tuple = ()):
    """Registra a rota no blueprint e a descreve no OpenAPI.

    A função decorada retorna um objeto serializável em JSON (ou nada, para 204).
    """

    def decorador(func):
        @functools.wraps(func)
        def view(*args, **kwargs):
            if protegida:
                exigir_admin()
            resultado = func(*args, **kwargs)
            if status == 204:
                return "", 204
            return jsonify(resultado), status

        bp.add_url_rule(regra, endpoint=func.__name__, view_func=view, methods=[metodo])
        REGISTRO.append(OperacaoDoc(
            regra=(bp.url_prefix or "") + regra, metodo=metodo.lower(), resumo=resumo, tag=tag,
            requisicao=requisicao, status=status, resposta=resposta, protegida=protegida,
            consulta=consulta))
        return view

    return decorador
