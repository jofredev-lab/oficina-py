"""Implementação das portas de persistência com SQLAlchemy (PostgreSQL em produção)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.application.ports import (
    ClienteRepository, OrdemServicoRepository, PecaRepository, ServicoRepository, UnitOfWork,
    VeiculoRepository,
)
from app.domain.cliente import Cliente, Documento
from app.domain.ordem_servico import (
    ItemPeca, ItemServico, OrcamentoStatus, OrdemServico, StatusOS,
)
from app.domain.peca import Peca
from app.domain.servico import Servico
from app.domain.shared import ConflitoError
from app.domain.veiculo import Placa, Veiculo

from .models import (
    ClienteModel, ItemPecaModel, ItemServicoModel, OrdemServicoModel, PecaModel, ServicoModel,
    VeiculoModel,
)


def _aware(valor: datetime | None) -> datetime | None:
    """Garante datetimes com fuso (alguns bancos, como SQLite, devolvem valores 'naive')."""
    if valor is not None and valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor


class _RepositorioBase:
    def __init__(self, session: Session) -> None:
        self._s = session

    def _flush(self, mensagem_conflito: str) -> None:
        try:
            self._s.flush()
        except IntegrityError as e:
            raise ConflitoError(mensagem_conflito) from e
        except StaleDataError as e:
            raise ConflitoError("Registro alterado por outra operação; tente novamente") from e


class SqlAlchemyClienteRepository(_RepositorioBase, ClienteRepository):
    @staticmethod
    def _para_dominio(m: ClienteModel) -> Cliente:
        return Cliente(m.nome, Documento(m.documento), m.email, m.telefone, id=m.id)

    def save(self, cliente: Cliente) -> Cliente:
        m = self._s.get(ClienteModel, cliente.id) if cliente.id is not None else None
        if m is None:
            m = ClienteModel()
            self._s.add(m)
        m.nome = cliente.nome
        m.documento = cliente.documento.numero
        m.email = cliente.email
        m.telefone = cliente.telefone
        self._flush("CPF/CNPJ já cadastrado")
        cliente.id = m.id
        return cliente

    def get(self, id: int) -> Optional[Cliente]:
        m = self._s.get(ClienteModel, id)
        return self._para_dominio(m) if m else None

    def get_by_documento(self, numero: str) -> Optional[Cliente]:
        m = self._s.scalars(select(ClienteModel).where(ClienteModel.documento == numero)).first()
        return self._para_dominio(m) if m else None

    def list_all(self) -> list[Cliente]:
        return [self._para_dominio(m) for m in self._s.scalars(select(ClienteModel).order_by(ClienteModel.id))]

    def delete(self, id: int) -> None:
        m = self._s.get(ClienteModel, id)
        if m is not None:
            self._s.delete(m)
            self._flush("Cliente possui veículos ou ordens de serviço vinculados")


class SqlAlchemyVeiculoRepository(_RepositorioBase, VeiculoRepository):
    @staticmethod
    def _para_dominio(m: VeiculoModel) -> Veiculo:
        return Veiculo(Placa(m.placa), m.marca, m.modelo, m.ano, m.cliente_id, id=m.id)

    def save(self, veiculo: Veiculo) -> Veiculo:
        m = self._s.get(VeiculoModel, veiculo.id) if veiculo.id is not None else None
        if m is None:
            m = VeiculoModel()
            self._s.add(m)
        m.placa = veiculo.placa.numero
        m.marca = veiculo.marca
        m.modelo = veiculo.modelo
        m.ano = veiculo.ano
        m.cliente_id = veiculo.cliente_id
        self._flush("Placa já cadastrada")
        veiculo.id = m.id
        return veiculo

    def get(self, id: int) -> Optional[Veiculo]:
        m = self._s.get(VeiculoModel, id)
        return self._para_dominio(m) if m else None

    def get_by_placa(self, numero: str) -> Optional[Veiculo]:
        m = self._s.scalars(select(VeiculoModel).where(VeiculoModel.placa == numero)).first()
        return self._para_dominio(m) if m else None

    def list_all(self, cliente_id: Optional[int] = None) -> list[Veiculo]:
        consulta = select(VeiculoModel).order_by(VeiculoModel.id)
        if cliente_id is not None:
            consulta = consulta.where(VeiculoModel.cliente_id == cliente_id)
        return [self._para_dominio(m) for m in self._s.scalars(consulta)]

    def delete(self, id: int) -> None:
        m = self._s.get(VeiculoModel, id)
        if m is not None:
            self._s.delete(m)
            self._flush("Veículo possui ordens de serviço vinculadas")


class SqlAlchemyServicoRepository(_RepositorioBase, ServicoRepository):
    @staticmethod
    def _para_dominio(m: ServicoModel) -> Servico:
        return Servico(m.nome, m.descricao, m.preco, id=m.id)

    def save(self, servico: Servico) -> Servico:
        m = self._s.get(ServicoModel, servico.id) if servico.id is not None else None
        if m is None:
            m = ServicoModel()
            self._s.add(m)
        m.nome = servico.nome
        m.descricao = servico.descricao
        m.preco = servico.preco
        self._flush("Conflito ao salvar serviço")
        servico.id = m.id
        return servico

    def get(self, id: int) -> Optional[Servico]:
        m = self._s.get(ServicoModel, id)
        return self._para_dominio(m) if m else None

    def list_all(self) -> list[Servico]:
        return [self._para_dominio(m) for m in self._s.scalars(select(ServicoModel).order_by(ServicoModel.id))]

    def delete(self, id: int) -> None:
        m = self._s.get(ServicoModel, id)
        if m is not None:
            self._s.delete(m)
            self._flush("Serviço está em uso em ordens de serviço")


class SqlAlchemyPecaRepository(_RepositorioBase, PecaRepository):
    @staticmethod
    def _para_dominio(m: PecaModel) -> Peca:
        return Peca(m.codigo, m.nome, m.preco, m.quantidade_estoque, m.estoque_minimo, id=m.id)

    def save(self, peca: Peca) -> Peca:
        m = self._s.get(PecaModel, peca.id) if peca.id is not None else None
        if m is None:
            m = PecaModel()
            self._s.add(m)
        m.codigo = peca.codigo
        m.nome = peca.nome
        m.preco = peca.preco
        m.quantidade_estoque = peca.quantidade_estoque
        m.estoque_minimo = peca.estoque_minimo
        self._flush("Código de peça já cadastrado")
        peca.id = m.id
        return peca

    def get(self, id: int) -> Optional[Peca]:
        m = self._s.get(PecaModel, id)
        return self._para_dominio(m) if m else None

    def get_by_codigo(self, codigo: str) -> Optional[Peca]:
        m = self._s.scalars(select(PecaModel).where(PecaModel.codigo == codigo)).first()
        return self._para_dominio(m) if m else None

    def list_all(self) -> list[Peca]:
        return [self._para_dominio(m) for m in self._s.scalars(select(PecaModel).order_by(PecaModel.id))]

    def delete(self, id: int) -> None:
        m = self._s.get(PecaModel, id)
        if m is not None:
            self._s.delete(m)
            self._flush("Peça está em uso em ordens de serviço")


class SqlAlchemyOrdemServicoRepository(_RepositorioBase, OrdemServicoRepository):
    @staticmethod
    def _para_dominio(m: OrdemServicoModel) -> OrdemServico:
        return OrdemServico(
            id=m.id,
            cliente_id=m.cliente_id,
            veiculo_id=m.veiculo_id,
            codigo_acompanhamento=m.codigo_acompanhamento,
            status=StatusOS[m.status],
            orcamento_status=OrcamentoStatus[m.orcamento_status],
            criada_em=_aware(m.criada_em),
            servicos=[ItemServico(i.servico_id, i.nome_servico, i.preco) for i in m.servicos],
            pecas=[ItemPeca(i.peca_id, i.nome_peca, i.preco_unitario, i.quantidade) for i in m.pecas],
            inicio_execucao_em=_aware(m.inicio_execucao_em),
            fim_execucao_em=_aware(m.fim_execucao_em),
            entregue_em=_aware(m.entregue_em),
        )

    def save(self, ordem: OrdemServico) -> OrdemServico:
        m = self._s.get(OrdemServicoModel, ordem.id) if ordem.id is not None else None
        if m is None:
            m = OrdemServicoModel(codigo_acompanhamento=ordem.codigo_acompanhamento)
            self._s.add(m)
        m.cliente_id = ordem.cliente_id
        m.veiculo_id = ordem.veiculo_id
        m.status = ordem.status.name
        m.orcamento_status = ordem.orcamento_status.name
        m.criada_em = ordem.criada_em
        m.inicio_execucao_em = ordem.inicio_execucao_em
        m.fim_execucao_em = ordem.fim_execucao_em
        m.entregue_em = ordem.entregue_em
        # itens são append-only: persiste apenas os novos
        for item in ordem.servicos[len(m.servicos):]:
            m.servicos.append(ItemServicoModel(
                servico_id=item.servico_id, nome_servico=item.nome_servico, preco=item.preco))
        for item in ordem.pecas[len(m.pecas):]:
            m.pecas.append(ItemPecaModel(
                peca_id=item.peca_id, nome_peca=item.nome_peca,
                preco_unitario=item.preco_unitario, quantidade=item.quantidade))
        self._flush("Conflito ao salvar ordem de serviço")
        ordem.id = m.id
        return ordem

    def get(self, id: int) -> Optional[OrdemServico]:
        m = self._s.get(OrdemServicoModel, id)
        return self._para_dominio(m) if m else None

    def get_by_codigo(self, codigo: str) -> Optional[OrdemServico]:
        m = self._s.scalars(
            select(OrdemServicoModel).where(OrdemServicoModel.codigo_acompanhamento == codigo)).first()
        return self._para_dominio(m) if m else None

    def list_all(self, status: Optional[StatusOS] = None) -> list[OrdemServico]:
        consulta = select(OrdemServicoModel).order_by(OrdemServicoModel.criada_em, OrdemServicoModel.id)
        if status is not None:
            consulta = consulta.where(OrdemServicoModel.status == status.name)
        return [self._para_dominio(m) for m in self._s.scalars(consulta)]

    def list_executadas(self) -> list[OrdemServico]:
        consulta = select(OrdemServicoModel).where(
            OrdemServicoModel.inicio_execucao_em.is_not(None),
            OrdemServicoModel.fim_execucao_em.is_not(None))
        return [self._para_dominio(m) for m in self._s.scalars(consulta)]


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Uma sessão = uma transação. Commit ao sair sem erro; rollback em caso de exceção."""

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.clientes = SqlAlchemyClienteRepository(self._session)
        self.veiculos = SqlAlchemyVeiculoRepository(self._session)
        self.servicos = SqlAlchemyServicoRepository(self._session)
        self.pecas = SqlAlchemyPecaRepository(self._session)
        self.ordens = SqlAlchemyOrdemServicoRepository(self._session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        session = self._session
        try:
            if exc_type is None:
                try:
                    session.commit()
                except IntegrityError as e:
                    session.rollback()
                    raise ConflitoError("Operação viola uma restrição de integridade dos dados") from e
                except StaleDataError as e:
                    session.rollback()
                    raise ConflitoError("Registro alterado por outra operação; tente novamente") from e
            else:
                session.rollback()
        finally:
            session.close()
            self._session = None
