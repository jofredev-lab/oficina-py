from flask import Blueprint, request

from app.interfaces.serializers import servico_json
from app.interfaces.validation import corpo_json, parse_servico

from .support import container, endpoint

bp = Blueprint("servicos", __name__, url_prefix="/api/admin/servicos")
TAG = "Serviços"


@endpoint(bp, "", "POST", resumo="Cadastra serviço do catálogo", tag=TAG, status=201,
          requisicao="ServicoRequest", resposta="Servico")
def criar():
    return servico_json(container().servicos.criar(parse_servico(corpo_json(request))))


@endpoint(bp, "", "GET", resumo="Lista serviços", tag=TAG, resposta="Servico[]")
def listar():
    return [servico_json(s) for s in container().servicos.listar()]


@endpoint(bp, "/<int:id>", "GET", resumo="Detalha serviço", tag=TAG, resposta="Servico")
def buscar(id):
    return servico_json(container().servicos.buscar(id))


@endpoint(bp, "/<int:id>", "PUT", resumo="Atualiza serviço", tag=TAG,
          requisicao="ServicoRequest", resposta="Servico")
def atualizar(id):
    return servico_json(container().servicos.atualizar(id, parse_servico(corpo_json(request))))


@endpoint(bp, "/<int:id>", "DELETE", resumo="Remove serviço", tag=TAG, status=204)
def remover(id):
    container().servicos.remover(id)
