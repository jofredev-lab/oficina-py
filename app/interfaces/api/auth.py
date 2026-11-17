from flask import Blueprint, request

from app.interfaces.validation import corpo_json, parse_login

from .support import container, endpoint

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@endpoint(bp, "/login", "POST", resumo="Autentica o administrador e retorna um token JWT",
          tag="Autenticação", requisicao="LoginRequest", resposta="Token", protegida=False)
def login():
    username, password = parse_login(corpo_json(request))
    token, expira_em = container().auth.autenticar(username, password)
    return {"token": token, "tipo": "Bearer", "expiraEmSegundos": expira_em}
