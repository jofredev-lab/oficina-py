from flask import Blueprint, request

from app.interfaces.serializers import cliente_json
from app.interfaces.validation import corpo_json, parse_cliente

from .support import container, endpoint

bp = Blueprint("clientes", __name__, url_prefix="/api/admin/clientes")
TAG = "Clientes"


@endpoint(bp, "", "POST", resumo="Cadastra cliente (valida CPF/CNPJ)", tag=TAG, status=201,
          requisicao="ClienteRequest", resposta="Cliente")
def criar():
    return cliente_json(container().clientes.criar(parse_cliente(corpo_json(request))))


@endpoint(bp, "", "GET", resumo="Lista clientes", tag=TAG, resposta="Cliente[]")
def listar():
    return [cliente_json(c) for c in container().clientes.listar()]


@endpoint(bp, "/<int:id>", "GET", resumo="Detalha cliente", tag=TAG, resposta="Cliente")
def buscar(id):
    return cliente_json(container().clientes.buscar(id))


@endpoint(bp, "/<int:id>", "PUT", resumo="Atualiza cliente", tag=TAG,
          requisicao="ClienteRequest", resposta="Cliente")
def atualizar(id):
    return cliente_json(container().clientes.atualizar(id, parse_cliente(corpo_json(request))))


@endpoint(bp, "/<int:id>", "DELETE", resumo="Remove cliente (409 se houver veículos/OS vinculados)",
          tag=TAG, status=204)
def remover(id):
    container().clientes.remover(id)
