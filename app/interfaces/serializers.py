"""Conversão dos objetos de domínio para JSON (contrato camelCase da API)."""
from __future__ import annotations

from app.application.views import OrdemServicoView, TempoMedioExecucao
from app.domain.cliente import Cliente
from app.domain.ordem_servico import ItemPeca, ItemServico
from app.domain.peca import Peca
from app.domain.servico import Servico
from app.domain.veiculo import Veiculo


def _dinheiro(valor) -> float:
    return float(valor)


def _iso(valor):
    return valor.isoformat() if valor is not None else None


def cliente_json(c: Cliente) -> dict:
    return {"id": c.id, "nome": c.nome, "documento": c.documento.numero,
            "tipoDocumento": c.documento.tipo.value, "email": c.email, "telefone": c.telefone}


def veiculo_json(v: Veiculo) -> dict:
    return {"id": v.id, "placa": v.placa.numero, "marca": v.marca, "modelo": v.modelo,
            "ano": v.ano, "clienteId": v.cliente_id}


def servico_json(s: Servico) -> dict:
    return {"id": s.id, "nome": s.nome, "descricao": s.descricao, "preco": _dinheiro(s.preco)}


def peca_json(p: Peca) -> dict:
    return {"id": p.id, "codigo": p.codigo, "nome": p.nome, "preco": _dinheiro(p.preco),
            "quantidadeEstoque": p.quantidade_estoque, "estoqueMinimo": p.estoque_minimo,
            "estoqueBaixo": p.estoque_baixo}


def _item_servico_json(i: ItemServico) -> dict:
    return {"servicoId": i.servico_id, "nome": i.nome_servico, "preco": _dinheiro(i.preco)}


def _item_peca_json(i: ItemPeca) -> dict:
    return {"pecaId": i.peca_id, "nome": i.nome_peca, "precoUnitario": _dinheiro(i.preco_unitario),
            "quantidade": i.quantidade, "subtotal": _dinheiro(i.subtotal)}


def ordem_json(view: OrdemServicoView) -> dict:
    o, c, v = view.ordem, view.cliente, view.veiculo
    return {
        "id": o.id,
        "codigoAcompanhamento": o.codigo_acompanhamento,
        "clienteId": c.id,
        "clienteNome": c.nome,
        "clienteDocumento": c.documento.numero,
        "veiculoPlaca": v.placa.numero,
        "veiculoMarca": v.marca,
        "veiculoModelo": v.modelo,
        "veiculoAno": v.ano,
        "status": o.status.name,
        "statusDescricao": o.status.descricao,
        "orcamentoStatus": o.orcamento_status.name,
        "servicos": [_item_servico_json(i) for i in o.servicos],
        "pecas": [_item_peca_json(i) for i in o.pecas],
        "valorServicos": _dinheiro(o.valor_servicos),
        "valorPecas": _dinheiro(o.valor_pecas),
        "valorTotal": _dinheiro(o.valor_total),
        "criadaEm": _iso(o.criada_em),
        "inicioExecucaoEm": _iso(o.inicio_execucao_em),
        "fimExecucaoEm": _iso(o.fim_execucao_em),
        "entregueEm": _iso(o.entregue_em),
    }


def acompanhamento_json(view: OrdemServicoView) -> dict:
    """Visão pública para o cliente: não expõe dados pessoais."""
    o, v = view.ordem, view.veiculo
    return {
        "codigoAcompanhamento": o.codigo_acompanhamento,
        "status": o.status.name,
        "statusDescricao": o.status.descricao,
        "veiculoPlaca": v.placa.numero,
        "veiculoModelo": v.modelo,
        "orcamentoStatus": o.orcamento_status.name,
        "servicos": [_item_servico_json(i) for i in o.servicos],
        "pecas": [_item_peca_json(i) for i in o.pecas],
        "valorTotal": _dinheiro(o.valor_total),
        "criadaEm": _iso(o.criada_em),
        "inicioExecucaoEm": _iso(o.inicio_execucao_em),
        "fimExecucaoEm": _iso(o.fim_execucao_em),
        "entregueEm": _iso(o.entregue_em),
    }


def tempo_medio_json(t: TempoMedioExecucao) -> dict:
    return {"quantidadeOrdens": t.quantidade_ordens, "tempoMedioMinutos": t.tempo_medio_minutos,
            "tempoMedioFormatado": t.tempo_medio_formatado}
