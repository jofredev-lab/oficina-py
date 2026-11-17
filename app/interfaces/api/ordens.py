from flask import Blueprint, request

from app.domain.ordem_servico import StatusOS
from app.interfaces.serializers import ordem_json
from app.interfaces.validation import ValidationError, corpo_json, parse_abrir_os, parse_itens

from .support import container, endpoint

bp = Blueprint("ordens", __name__, url_prefix="/api/admin/ordens-servico")
TAG = "Ordens de serviço"


def _parse_status(valor: str | None) -> StatusOS | None:
    if not valor:
        return None
    try:
        return StatusOS[valor.upper()]
    except KeyError:
        raise ValidationError({"status": "valor inválido; use um de: " + ", ".join(s.name for s in StatusOS)}) from None


@endpoint(bp, "", "POST",
          resumo="Abre uma OS: identifica o cliente por CPF/CNPJ, cadastra/reutiliza o veículo e inclui serviços e peças",
          tag=TAG, status=201, requisicao="AbrirOrdemServicoRequest", resposta="OrdemServico")
def abrir():
    return ordem_json(container().ordens.abrir(parse_abrir_os(corpo_json(request))))


@endpoint(bp, "", "GET", resumo="Lista OS em ordem de chegada, com filtro opcional por status", tag=TAG,
          resposta="OrdemServico[]",
          consulta=(("status", {"type": "string", "enum": [s.name for s in StatusOS]},
                     "Filtra pelo status da OS"),))
def listar():
    status = _parse_status(request.args.get("status"))
    return [ordem_json(v) for v in container().ordens.listar(status)]


@endpoint(bp, "/<int:id>", "GET", resumo="Detalha OS (itens, orçamento e datas)", tag=TAG,
          resposta="OrdemServico")
def buscar(id):
    return ordem_json(container().ordens.buscar(id))


@endpoint(bp, "/<int:id>/itens", "POST", resumo="Inclui serviços/peças (somente em Recebida ou Em diagnóstico)",
          tag=TAG, requisicao="AdicionarItensRequest", resposta="OrdemServico")
def adicionar_itens(id):
    return ordem_json(container().ordens.adicionar_itens(id, parse_itens(corpo_json(request))))


@endpoint(bp, "/<int:id>/diagnostico", "POST", resumo="Recebida -> Em diagnóstico", tag=TAG,
          resposta="OrdemServico")
def iniciar_diagnostico(id):
    return ordem_json(container().ordens.iniciar_diagnostico(id))


@endpoint(bp, "/<int:id>/orcamento/enviar", "POST",
          resumo="Gera o orçamento e envia ao cliente: Em diagnóstico -> Aguardando aprovação", tag=TAG,
          resposta="OrdemServico")
def enviar_orcamento(id):
    return ordem_json(container().ordens.enviar_orcamento(id))


@endpoint(bp, "/<int:id>/orcamento/aprovar", "POST",
          resumo="Registra aprovação (balcão): Aguardando aprovação -> Em execução, com baixa de estoque",
          tag=TAG, resposta="OrdemServico")
def aprovar(id):
    return ordem_json(container().ordens.aprovar_orcamento(id))


@endpoint(bp, "/<int:id>/orcamento/rejeitar", "POST",
          resumo="Registra rejeição (balcão): Aguardando aprovação -> Finalizada, sem execução", tag=TAG,
          resposta="OrdemServico")
def rejeitar(id):
    return ordem_json(container().ordens.rejeitar_orcamento(id))


@endpoint(bp, "/<int:id>/finalizar", "POST", resumo="Em execução -> Finalizada", tag=TAG,
          resposta="OrdemServico")
def finalizar(id):
    return ordem_json(container().ordens.finalizar(id))


@endpoint(bp, "/<int:id>/entregar", "POST", resumo="Finalizada -> Entregue", tag=TAG,
          resposta="OrdemServico")
def entregar(id):
    return ordem_json(container().ordens.entregar(id))
