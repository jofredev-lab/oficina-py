from flask import Blueprint, request

from app.interfaces.serializers import veiculo_json
from app.interfaces.validation import ValidationError, corpo_json, parse_veiculo

from .support import container, endpoint

bp = Blueprint("veiculos", __name__, url_prefix="/api/admin/veiculos")
TAG = "Veículos"


@endpoint(bp, "", "POST", resumo="Cadastra veículo (valida placa)", tag=TAG, status=201,
          requisicao="VeiculoRequest", resposta="Veiculo")
def criar():
    return veiculo_json(container().veiculos.criar(parse_veiculo(corpo_json(request))))


@endpoint(bp, "", "GET", resumo="Lista veículos, com filtro opcional por cliente", tag=TAG,
          resposta="Veiculo[]",
          consulta=(("clienteId", {"type": "integer"}, "Filtra pelos veículos do cliente"),))
def listar():
    cliente_id = request.args.get("clienteId")
    if cliente_id is not None:
        try:
            cliente_id = int(cliente_id)
        except ValueError:
            raise ValidationError({"clienteId": "deve ser um número inteiro"}) from None
    return [veiculo_json(v) for v in container().veiculos.listar(cliente_id)]


@endpoint(bp, "/<int:id>", "GET", resumo="Detalha veículo", tag=TAG, resposta="Veiculo")
def buscar(id):
    return veiculo_json(container().veiculos.buscar(id))


@endpoint(bp, "/<int:id>", "PUT", resumo="Atualiza veículo", tag=TAG,
          requisicao="VeiculoRequest", resposta="Veiculo")
def atualizar(id):
    return veiculo_json(container().veiculos.atualizar(id, parse_veiculo(corpo_json(request))))


@endpoint(bp, "/<int:id>", "DELETE", resumo="Remove veículo", tag=TAG, status=204)
def remover(id):
    container().veiculos.remover(id)
