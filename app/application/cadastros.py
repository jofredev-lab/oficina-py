"""Casos de uso de cadastros: clientes, veículos, serviços e peças/insumos."""
from __future__ import annotations

from typing import Callable

from app.domain.cliente import Cliente, Documento
from app.domain.peca import Peca
from app.domain.servico import Servico
from app.domain.shared import ConflitoError, RecursoNaoEncontradoError
from app.domain.veiculo import Placa, Veiculo

from .commands import ClienteDados, PecaDados, ServicoDados, VeiculoDados
from .ports import UnitOfWork

UowFactory = Callable[[], UnitOfWork]


class ClienteService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow = uow_factory

    def criar(self, d: ClienteDados) -> Cliente:
        documento = Documento.of(d.documento)
        with self._uow() as uow:
            if uow.clientes.get_by_documento(documento.numero):
                raise ConflitoError("Já existe um cliente com este CPF/CNPJ")
            return uow.clientes.save(Cliente(d.nome, documento, d.email, d.telefone))

    def listar(self) -> list[Cliente]:
        with self._uow() as uow:
            return uow.clientes.list_all()

    def buscar(self, id: int) -> Cliente:
        with self._uow() as uow:
            return _obter_cliente(uow, id)

    def atualizar(self, id: int, d: ClienteDados) -> Cliente:
        documento = Documento.of(d.documento)
        with self._uow() as uow:
            cliente = _obter_cliente(uow, id)
            outro = uow.clientes.get_by_documento(documento.numero)
            if outro is not None and outro.id != id:
                raise ConflitoError("Já existe outro cliente com este CPF/CNPJ")
            cliente.atualizar(d.nome, documento, d.email, d.telefone)
            return uow.clientes.save(cliente)

    def remover(self, id: int) -> None:
        with self._uow() as uow:
            _obter_cliente(uow, id)
            uow.clientes.delete(id)


class VeiculoService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow = uow_factory

    def criar(self, d: VeiculoDados) -> Veiculo:
        placa = Placa.of(d.placa)
        with self._uow() as uow:
            if uow.veiculos.get_by_placa(placa.numero):
                raise ConflitoError("Já existe um veículo com esta placa")
            _obter_cliente(uow, d.cliente_id)
            return uow.veiculos.save(Veiculo(placa, d.marca, d.modelo, d.ano, d.cliente_id))

    def listar(self, cliente_id: int | None = None) -> list[Veiculo]:
        with self._uow() as uow:
            return uow.veiculos.list_all(cliente_id)

    def buscar(self, id: int) -> Veiculo:
        with self._uow() as uow:
            return _obter_veiculo(uow, id)

    def atualizar(self, id: int, d: VeiculoDados) -> Veiculo:
        placa = Placa.of(d.placa)
        with self._uow() as uow:
            veiculo = _obter_veiculo(uow, id)
            outro = uow.veiculos.get_by_placa(placa.numero)
            if outro is not None and outro.id != id:
                raise ConflitoError("Já existe outro veículo com esta placa")
            _obter_cliente(uow, d.cliente_id)
            veiculo.atualizar(placa, d.marca, d.modelo, d.ano, d.cliente_id)
            return uow.veiculos.save(veiculo)

    def remover(self, id: int) -> None:
        with self._uow() as uow:
            _obter_veiculo(uow, id)
            uow.veiculos.delete(id)


class ServicoService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow = uow_factory

    def criar(self, d: ServicoDados) -> Servico:
        with self._uow() as uow:
            return uow.servicos.save(Servico(d.nome, d.descricao, d.preco))

    def listar(self) -> list[Servico]:
        with self._uow() as uow:
            return uow.servicos.list_all()

    def buscar(self, id: int) -> Servico:
        with self._uow() as uow:
            return _obter_servico(uow, id)

    def atualizar(self, id: int, d: ServicoDados) -> Servico:
        with self._uow() as uow:
            servico = _obter_servico(uow, id)
            servico.atualizar(d.nome, d.descricao, d.preco)
            return uow.servicos.save(servico)

    def remover(self, id: int) -> None:
        with self._uow() as uow:
            _obter_servico(uow, id)
            uow.servicos.delete(id)


class PecaService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow = uow_factory

    def criar(self, d: PecaDados) -> Peca:
        nova = Peca(d.codigo, d.nome, d.preco, d.quantidade_estoque, d.estoque_minimo)
        with self._uow() as uow:
            if uow.pecas.get_by_codigo(nova.codigo):
                raise ConflitoError(f"Já existe uma peça com o código {nova.codigo}")
            return uow.pecas.save(nova)

    def listar(self) -> list[Peca]:
        with self._uow() as uow:
            return uow.pecas.list_all()

    def listar_com_estoque_baixo(self) -> list[Peca]:
        with self._uow() as uow:
            return [p for p in uow.pecas.list_all() if p.estoque_baixo]

    def buscar(self, id: int) -> Peca:
        with self._uow() as uow:
            return _obter_peca(uow, id)

    def atualizar(self, id: int, d: PecaDados) -> Peca:
        with self._uow() as uow:
            peca = _obter_peca(uow, id)
            codigo = d.codigo.strip().upper()
            outra = uow.pecas.get_by_codigo(codigo)
            if outra is not None and outra.id != id:
                raise ConflitoError(f"Já existe outra peça com o código {codigo}")
            peca.atualizar(d.codigo, d.nome, d.preco, d.quantidade_estoque, d.estoque_minimo)
            return uow.pecas.save(peca)

    def registrar_entrada(self, id: int, quantidade: int) -> Peca:
        with self._uow() as uow:
            peca = _obter_peca(uow, id)
            peca.repor_estoque(quantidade)
            return uow.pecas.save(peca)

    def registrar_saida(self, id: int, quantidade: int) -> Peca:
        with self._uow() as uow:
            peca = _obter_peca(uow, id)
            peca.baixar_estoque(quantidade)
            return uow.pecas.save(peca)

    def remover(self, id: int) -> None:
        with self._uow() as uow:
            _obter_peca(uow, id)
            uow.pecas.delete(id)


def _obter_cliente(uow: UnitOfWork, id: int) -> Cliente:
    cliente = uow.clientes.get(id)
    if cliente is None:
        raise RecursoNaoEncontradoError(f"Cliente não encontrado: {id}")
    return cliente


def _obter_veiculo(uow: UnitOfWork, id: int) -> Veiculo:
    veiculo = uow.veiculos.get(id)
    if veiculo is None:
        raise RecursoNaoEncontradoError(f"Veículo não encontrado: {id}")
    return veiculo


def _obter_servico(uow: UnitOfWork, id: int) -> Servico:
    servico = uow.servicos.get(id)
    if servico is None:
        raise RecursoNaoEncontradoError(f"Serviço não encontrado: {id}")
    return servico


def _obter_peca(uow: UnitOfWork, id: int) -> Peca:
    peca = uow.pecas.get(id)
    if peca is None:
        raise RecursoNaoEncontradoError(f"Peça não encontrada: {id}")
    return peca
