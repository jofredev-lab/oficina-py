"""API pública usada pelo aplicativo do cliente. O código de acompanhamento (UUID) é o segredo de acesso."""
from flask import Blueprint

from app.interfaces.serializers import acompanhamento_json

from .support import container, endpoint

bp = Blueprint("acompanhamento", __name__, url_prefix="/api/public/acompanhamento")
TAG = "Acompanhamento do cliente"


@endpoint(bp, "/<codigo>", "GET", resumo="Consulta o andamento da OS e o orçamento", tag=TAG,
          resposta="Acompanhamento", protegida=False)
def consultar(codigo):
    return acompanhamento_json(container().ordens.consultar_acompanhamento(codigo))


@endpoint(bp, "/<codigo>/orcamento/aprovar", "POST",
          resumo="Cliente aprova o orçamento (inicia a execução e baixa o estoque)", tag=TAG,
          resposta="Acompanhamento", protegida=False)
def aprovar(codigo):
    return acompanhamento_json(container().ordens.aprovar_por_codigo(codigo))


@endpoint(bp, "/<codigo>/orcamento/rejeitar", "POST",
          resumo="Cliente rejeita o orçamento (OS é finalizada sem execução)", tag=TAG,
          resposta="Acompanhamento", protegida=False)
def rejeitar(codigo):
    return acompanhamento_json(container().ordens.rejeitar_por_codigo(codigo))
