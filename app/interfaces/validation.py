"""Validação leve dos corpos JSON (tipos, obrigatoriedade, limites). Regras de negócio ficam no domínio."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.commands import (
    AbrirOrdemServicoDados, ClienteDados, ItemPecaDados, ItensDados, PecaDados, ServicoDados,
    VeiculoDados, VeiculoOSDados,
)

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    def __init__(self, erros: dict[str, str]) -> None:
        super().__init__("Dados inválidos")
        self.erros = erros


class Validator:
    def __init__(self, dados: dict, prefixo: str = "", erros: dict[str, str] | None = None) -> None:
        self.dados = dados
        self.prefixo = prefixo
        self.erros: dict[str, str] = erros if erros is not None else {}

    def _erro(self, campo: str, mensagem: str) -> None:
        self.erros.setdefault(self.prefixo + campo, mensagem)

    def _valor(self, campo: str, obrigatorio: bool) -> Any:
        valor = self.dados.get(campo)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            if obrigatorio:
                self._erro(campo, "campo obrigatório")
            return None
        return valor

    def texto(self, campo: str, obrigatorio: bool = True, max_len: int | None = None) -> str | None:
        valor = self._valor(campo, obrigatorio)
        if valor is None:
            return None
        if not isinstance(valor, str):
            self._erro(campo, "deve ser um texto")
            return None
        if max_len is not None and len(valor) > max_len:
            self._erro(campo, f"deve ter no máximo {max_len} caracteres")
            return None
        return valor

    def email(self, campo: str) -> str | None:
        valor = self.texto(campo, obrigatorio=False, max_len=150)
        if valor is not None and not _EMAIL.match(valor):
            self._erro(campo, "e-mail inválido")
            return None
        return valor

    def inteiro(self, campo: str, obrigatorio: bool = True, minimo: int | None = None) -> int | None:
        valor = self._valor(campo, obrigatorio)
        if valor is None:
            return None
        if isinstance(valor, bool) or not isinstance(valor, int):
            self._erro(campo, "deve ser um número inteiro")
            return None
        if minimo is not None and valor < minimo:
            self._erro(campo, f"deve ser maior ou igual a {minimo}")
            return None
        return valor

    def decimal(self, campo: str, obrigatorio: bool = True, minimo: Decimal = Decimal("0")) -> Decimal | None:
        valor = self._valor(campo, obrigatorio)
        if valor is None:
            return None
        if isinstance(valor, bool) or not isinstance(valor, (int, float, str)):
            self._erro(campo, "deve ser um número")
            return None
        try:
            numero = Decimal(str(valor))
        except InvalidOperation:
            self._erro(campo, "deve ser um número")
            return None
        if not numero.is_finite():
            self._erro(campo, "deve ser um número")
            return None
        if numero < minimo:
            self._erro(campo, f"deve ser maior ou igual a {minimo}")
            return None
        return numero

    def objeto(self, campo: str, obrigatorio: bool = True) -> dict | None:
        valor = self.dados.get(campo)
        if valor is None:
            if obrigatorio:
                self._erro(campo, "campo obrigatório")
            return None
        if not isinstance(valor, dict):
            self._erro(campo, "deve ser um objeto")
            return None
        return valor

    def lista(self, campo: str) -> list:
        valor = self.dados.get(campo)
        if valor is None:
            return []
        if not isinstance(valor, list):
            self._erro(campo, "deve ser uma lista")
            return []
        return valor

    def lista_inteiros(self, campo: str) -> tuple[int, ...]:
        resultado = []
        for indice, item in enumerate(self.lista(campo)):
            if isinstance(item, bool) or not isinstance(item, int):
                self._erro(f"{campo}[{indice}]", "deve ser um número inteiro")
            else:
                resultado.append(item)
        return tuple(resultado)

    def lancar_se_houver_erros(self) -> None:
        if self.erros:
            raise ValidationError(dict(self.erros))


def corpo_json(request) -> dict:
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ValidationError({"corpo": "JSON inválido ou ausente"})
    return dados


# ---------- parsers por caso de uso ----------

def parse_login(dados: dict) -> tuple[str, str]:
    v = Validator(dados)
    username = v.texto("username")
    password = v.texto("password")
    v.lancar_se_houver_erros()
    return username, password


def parse_cliente(dados: dict) -> ClienteDados:
    v = Validator(dados)
    nome = v.texto("nome", max_len=150)
    documento = v.texto("documento", max_len=30)
    email = v.email("email")
    telefone = v.texto("telefone", obrigatorio=False, max_len=20)
    v.lancar_se_houver_erros()
    return ClienteDados(nome, documento, email, telefone)


def parse_veiculo(dados: dict) -> VeiculoDados:
    v = Validator(dados)
    placa = v.texto("placa", max_len=20)
    marca = v.texto("marca", max_len=60)
    modelo = v.texto("modelo", max_len=60)
    ano = v.inteiro("ano")
    cliente_id = v.inteiro("clienteId")
    v.lancar_se_houver_erros()
    return VeiculoDados(placa, marca, modelo, ano, cliente_id)


def parse_servico(dados: dict) -> ServicoDados:
    v = Validator(dados)
    nome = v.texto("nome", max_len=120)
    descricao = v.texto("descricao", obrigatorio=False, max_len=500)
    preco = v.decimal("preco")
    v.lancar_se_houver_erros()
    return ServicoDados(nome, descricao, preco)


def parse_peca(dados: dict) -> PecaDados:
    v = Validator(dados)
    codigo = v.texto("codigo", max_len=40)
    nome = v.texto("nome", max_len=120)
    preco = v.decimal("preco")
    estoque = v.inteiro("quantidadeEstoque", minimo=0)
    minimo = v.inteiro("estoqueMinimo", minimo=0)
    v.lancar_se_houver_erros()
    return PecaDados(codigo, nome, preco, estoque, minimo)


def parse_quantidade(dados: dict) -> int:
    v = Validator(dados)
    quantidade = v.inteiro("quantidade", minimo=1)
    v.lancar_se_houver_erros()
    return quantidade


def _parse_itens(v: Validator) -> ItensDados:
    servicos_ids = v.lista_inteiros("servicosIds")
    pecas = []
    for indice, item in enumerate(v.lista("pecas")):
        if not isinstance(item, dict):
            v._erro(f"pecas[{indice}]", "deve ser um objeto")
            continue
        sub = Validator(item, prefixo=f"pecas[{indice}].", erros=v.erros)
        peca_id = sub.inteiro("pecaId")
        quantidade = sub.inteiro("quantidade", minimo=1)
        if peca_id is not None and quantidade is not None:
            pecas.append(ItemPecaDados(peca_id, quantidade))
    return ItensDados(servicos_ids, tuple(pecas))


def parse_itens(dados: dict) -> ItensDados:
    v = Validator(dados)
    itens = _parse_itens(v)
    v.lancar_se_houver_erros()
    return itens


def parse_abrir_os(dados: dict) -> AbrirOrdemServicoDados:
    v = Validator(dados)
    documento = v.texto("documentoCliente", max_len=30)
    veiculo = None
    sub_dados = v.objeto("veiculo")
    if sub_dados is not None:
        sub = Validator(sub_dados, prefixo="veiculo.", erros=v.erros)
        placa = sub.texto("placa", max_len=20)
        marca = sub.texto("marca", max_len=60)
        modelo = sub.texto("modelo", max_len=60)
        ano = sub.inteiro("ano")
        veiculo = VeiculoOSDados(placa, marca, modelo, ano)
    itens = _parse_itens(v)
    v.lancar_se_houver_erros()
    return AbrirOrdemServicoDados(documento, veiculo, itens)
