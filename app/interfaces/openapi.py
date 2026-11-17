"""Gera a especificação OpenAPI 3 a partir das rotas registradas com ``@endpoint``."""
from __future__ import annotations

import re

from .api.support import OperacaoDoc

_S = {"type": "string"}
_I = {"type": "integer"}
_N = {"type": "number"}
_B = {"type": "boolean"}
_DT = {"type": "string", "format": "date-time", "nullable": True}


def _obj(props: dict, required: tuple = ()) -> dict:
    esquema = {"type": "object", "properties": props}
    if required:
        esquema["required"] = list(required)
    return esquema


def _ref(nome: str) -> dict:
    return {"$ref": f"#/components/schemas/{nome}"}


_ITEM_SERVICO = _obj({"servicoId": _I, "nome": _S, "preco": _N})
_ITEM_PECA = _obj({"pecaId": _I, "nome": _S, "precoUnitario": _N, "quantidade": _I, "subtotal": _N})
_PECA_ITEM_REQ = _obj({"pecaId": _I, "quantidade": {"type": "integer", "minimum": 1}}, ("pecaId", "quantidade"))
_VEICULO_OS_REQ = _obj({"placa": {"type": "string", "example": "ABC1D23"}, "marca": _S, "modelo": _S, "ano": _I},
                       ("placa", "marca", "modelo", "ano"))

SCHEMAS: dict = {
    "Problema": _obj({"type": _S, "title": _S, "status": _I, "detail": _S,
                      "erros": {"type": "object", "additionalProperties": _S}}),
    "LoginRequest": _obj({"username": {"type": "string", "example": "admin"},
                          "password": {"type": "string", "example": "admin123"}}, ("username", "password")),
    "Token": _obj({"token": _S, "tipo": _S, "expiraEmSegundos": _I}),
    "ClienteRequest": _obj({"nome": _S, "documento": {"type": "string", "example": "529.982.247-25"},
                            "email": _S, "telefone": _S}, ("nome", "documento")),
    "Cliente": _obj({"id": _I, "nome": _S, "documento": _S, "tipoDocumento": {"type": "string", "enum": ["CPF", "CNPJ"]},
                     "email": _S, "telefone": _S}),
    "VeiculoRequest": _obj({"placa": _S, "marca": _S, "modelo": _S, "ano": _I, "clienteId": _I},
                           ("placa", "marca", "modelo", "ano", "clienteId")),
    "Veiculo": _obj({"id": _I, "placa": _S, "marca": _S, "modelo": _S, "ano": _I, "clienteId": _I}),
    "ServicoRequest": _obj({"nome": _S, "descricao": _S, "preco": _N}, ("nome", "preco")),
    "Servico": _obj({"id": _I, "nome": _S, "descricao": _S, "preco": _N}),
    "PecaRequest": _obj({"codigo": _S, "nome": _S, "preco": _N, "quantidadeEstoque": _I, "estoqueMinimo": _I},
                        ("codigo", "nome", "preco", "quantidadeEstoque", "estoqueMinimo")),
    "Peca": _obj({"id": _I, "codigo": _S, "nome": _S, "preco": _N, "quantidadeEstoque": _I,
                  "estoqueMinimo": _I, "estoqueBaixo": _B}),
    "AjusteEstoqueRequest": _obj({"quantidade": {"type": "integer", "minimum": 1}}, ("quantidade",)),
    "AbrirOrdemServicoRequest": _obj({
        "documentoCliente": {"type": "string", "example": "529.982.247-25"},
        "veiculo": _VEICULO_OS_REQ,
        "servicosIds": {"type": "array", "items": _I},
        "pecas": {"type": "array", "items": _PECA_ITEM_REQ},
    }, ("documentoCliente", "veiculo")),
    "AdicionarItensRequest": _obj({"servicosIds": {"type": "array", "items": _I},
                                   "pecas": {"type": "array", "items": _PECA_ITEM_REQ}}),
    "OrdemServico": _obj({
        "id": _I, "codigoAcompanhamento": _S, "clienteId": _I, "clienteNome": _S, "clienteDocumento": _S,
        "veiculoPlaca": _S, "veiculoMarca": _S, "veiculoModelo": _S, "veiculoAno": _I,
        "status": {"type": "string", "enum": ["RECEBIDA", "EM_DIAGNOSTICO", "AGUARDANDO_APROVACAO",
                                              "EM_EXECUCAO", "FINALIZADA", "ENTREGUE"]},
        "statusDescricao": _S,
        "orcamentoStatus": {"type": "string", "enum": ["NAO_GERADO", "PENDENTE", "APROVADO", "REJEITADO"]},
        "servicos": {"type": "array", "items": _ITEM_SERVICO},
        "pecas": {"type": "array", "items": _ITEM_PECA},
        "valorServicos": _N, "valorPecas": _N, "valorTotal": _N,
        "criadaEm": _DT, "inicioExecucaoEm": _DT, "fimExecucaoEm": _DT, "entregueEm": _DT,
    }),
    "Acompanhamento": _obj({
        "codigoAcompanhamento": _S, "status": _S, "statusDescricao": _S, "veiculoPlaca": _S,
        "veiculoModelo": _S, "orcamentoStatus": _S,
        "servicos": {"type": "array", "items": _ITEM_SERVICO},
        "pecas": {"type": "array", "items": _ITEM_PECA}, "valorTotal": _N,
        "criadaEm": _DT, "inicioExecucaoEm": _DT, "fimExecucaoEm": _DT, "entregueEm": _DT,
    }),
    "TempoMedioExecucao": _obj({"quantidadeOrdens": _I, "tempoMedioMinutos": _N, "tempoMedioFormatado": _S}),
}

_PARAMETRO_DE_CAMINHO = re.compile(r"<(?:(\w+):)?(\w+)>")
_CONTEUDO_PROBLEMA = {"application/problem+json": {"schema": _ref("Problema")}}


def _esquema(nome: str) -> dict:
    if nome.endswith("[]"):
        return {"type": "array", "items": _ref(nome[:-2])}
    return _ref(nome)


def _operacao(op: OperacaoDoc) -> dict:
    parametros = [
        {"name": nome, "in": "path", "required": True,
         "schema": {"type": "integer"} if conversor == "int" else {"type": "string"}}
        for conversor, nome in _PARAMETRO_DE_CAMINHO.findall(op.regra)
    ]
    parametros += [{"name": nome, "in": "query", "required": False, "schema": esquema, "description": desc}
                   for nome, esquema, desc in op.consulta]

    respostas: dict = {}
    if op.status == 204:
        respostas["204"] = {"description": "Sem conteúdo"}
    else:
        respostas[str(op.status)] = {"description": "Sucesso"}
        if op.resposta:
            respostas[str(op.status)]["content"] = {"application/json": {"schema": _esquema(op.resposta)}}
    if op.requisicao or op.consulta:
        respostas["400"] = {"description": "Dados inválidos", "content": _CONTEUDO_PROBLEMA}
    if op.protegida:
        respostas["401"] = {"description": "Não autenticado", "content": _CONTEUDO_PROBLEMA}
    if _PARAMETRO_DE_CAMINHO.search(op.regra):
        respostas["404"] = {"description": "Não encontrado", "content": _CONTEUDO_PROBLEMA}
    if op.metodo in ("post", "put", "delete"):
        respostas["409"] = {"description": "Conflito", "content": _CONTEUDO_PROBLEMA}
        respostas["422"] = {"description": "Regra de negócio violada", "content": _CONTEUDO_PROBLEMA}

    operacao: dict = {"tags": [op.tag], "summary": op.resumo, "responses": respostas,
                      "security": [{"bearerAuth": []}] if op.protegida else []}
    if parametros:
        operacao["parameters"] = parametros
    if op.requisicao:
        operacao["requestBody"] = {"required": True, "content": {
            "application/json": {"schema": _ref(op.requisicao)}}}
    return operacao


def construir_openapi(registro: list[OperacaoDoc]) -> dict:
    caminhos: dict = {}
    for op in registro:
        caminho = _PARAMETRO_DE_CAMINHO.sub(r"{\2}", op.regra)
        caminhos.setdefault(caminho, {})[op.metodo] = _operacao(op)
    caminhos["/health"] = {"get": {
        "tags": ["Infra"], "summary": "Verificação de saúde da aplicação", "security": [],
        "responses": {"200": {"description": "Aplicação no ar"}}}}
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Oficina Mecânica - API (MVP)",
            "version": "1.0.0",
            "description": ("Gestão de ordens de serviço, clientes, veículos, serviços e peças. "
                            "Use POST /api/auth/login para obter o token e clique em Authorize."),
        },
        "paths": caminhos,
        "components": {
            "schemas": SCHEMAS,
            "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}},
        },
    }
