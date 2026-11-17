"""Modelos ORM (SQLAlchemy 2.x). São detalhe de infraestrutura: o domínio não os conhece."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ClienteModel(Base):
    __tablename__ = "cliente"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    documento: Mapped[str] = mapped_column(String(14), nullable=False, unique=True)
    email: Mapped[str | None] = mapped_column(String(150))
    telefone: Mapped[str | None] = mapped_column(String(20))


class VeiculoModel(Base):
    __tablename__ = "veiculo"

    id: Mapped[int] = mapped_column(primary_key=True)
    placa: Mapped[str] = mapped_column(String(7), nullable=False, unique=True)
    marca: Mapped[str] = mapped_column(String(60), nullable=False)
    modelo: Mapped[str] = mapped_column(String(60), nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), nullable=False)


class ServicoModel(Base):
    __tablename__ = "servico"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(500))
    preco: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)


class PecaModel(Base):
    __tablename__ = "peca"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    preco: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantidade_estoque: Mapped[int] = mapped_column(Integer, nullable=False)
    estoque_minimo: Mapped[int] = mapped_column(Integer, nullable=False)
    # lock otimista: evita baixas de estoque concorrentes inconsistentes
    versao: Mapped[int] = mapped_column(Integer, nullable=False)

    __mapper_args__ = {"version_id_col": versao}


class ItemServicoModel(Base):
    __tablename__ = "item_servico"

    id: Mapped[int] = mapped_column(primary_key=True)
    ordem_servico_id: Mapped[int] = mapped_column(ForeignKey("ordem_servico.id"), nullable=False)
    servico_id: Mapped[int] = mapped_column(ForeignKey("servico.id"), nullable=False)
    nome_servico: Mapped[str] = mapped_column(String(120), nullable=False)
    preco: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)


class ItemPecaModel(Base):
    __tablename__ = "item_peca"

    id: Mapped[int] = mapped_column(primary_key=True)
    ordem_servico_id: Mapped[int] = mapped_column(ForeignKey("ordem_servico.id"), nullable=False)
    peca_id: Mapped[int] = mapped_column(ForeignKey("peca.id"), nullable=False)
    nome_peca: Mapped[str] = mapped_column(String(120), nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)


class OrdemServicoModel(Base):
    __tablename__ = "ordem_servico"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_acompanhamento: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), nullable=False)
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculo.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    orcamento_status: Mapped[str] = mapped_column(String(20), nullable=False)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    inicio_execucao_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fim_execucao_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entregue_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    servicos: Mapped[list[ItemServicoModel]] = relationship(
        cascade="all, delete-orphan", order_by=ItemServicoModel.id, lazy="selectin")
    pecas: Mapped[list[ItemPecaModel]] = relationship(
        cascade="all, delete-orphan", order_by=ItemPecaModel.id, lazy="selectin")
