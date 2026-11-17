from flask import Blueprint, request

from app.interfaces.serializers import peca_json
from app.interfaces.validation import corpo_json, parse_peca, parse_quantidade

from .support import container, endpoint

bp = Blueprint("pecas", __name__, url_prefix="/api/admin/pecas")
TAG = "Peças e insumos"


@endpoint(bp, "", "POST", resumo="Cadastra peça/insumo", tag=TAG, status=201,
          requisicao="PecaRequest", resposta="Peca")
def criar():
    return peca_json(container().pecas.criar(parse_peca(corpo_json(request))))


@endpoint(bp, "", "GET", resumo="Lista peças e insumos", tag=TAG, resposta="Peca[]")
def listar():
    return [peca_json(p) for p in container().pecas.listar()]


@endpoint(bp, "/estoque-baixo", "GET", resumo="Lista peças com estoque igual ou abaixo do mínimo",
          tag=TAG, resposta="Peca[]")
def estoque_baixo():
    return [peca_json(p) for p in container().pecas.listar_com_estoque_baixo()]


@endpoint(bp, "/<int:id>", "GET", resumo="Detalha peça", tag=TAG, resposta="Peca")
def buscar(id):
    return peca_json(container().pecas.buscar(id))


@endpoint(bp, "/<int:id>", "PUT", resumo="Atualiza peça (inclui correção de estoque)", tag=TAG,
          requisicao="PecaRequest", resposta="Peca")
def atualizar(id):
    return peca_json(container().pecas.atualizar(id, parse_peca(corpo_json(request))))


@endpoint(bp, "/<int:id>/estoque/entrada", "POST", resumo="Registra entrada de estoque", tag=TAG,
          requisicao="AjusteEstoqueRequest", resposta="Peca")
def entrada(id):
    return peca_json(container().pecas.registrar_entrada(id, parse_quantidade(corpo_json(request))))


@endpoint(bp, "/<int:id>/estoque/saida", "POST",
          resumo="Registra saída manual de estoque (422 se não houver saldo)", tag=TAG,
          requisicao="AjusteEstoqueRequest", resposta="Peca")
def saida(id):
    return peca_json(container().pecas.registrar_saida(id, parse_quantidade(corpo_json(request))))


@endpoint(bp, "/<int:id>", "DELETE", resumo="Remove peça", tag=TAG, status=204)
def remover(id):
    container().pecas.remover(id)
