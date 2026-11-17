"""Agregado Ordem de Serviço: ciclo de vida, orçamento e regras de transição.

A baixa de estoque das peças é coordenada pela camada de aplicação, na mesma
unidade de trabalho (transação) da aprovação do orçamento.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum

from .peca import Peca
from .servico import Servico
from .shared import RegraNegocioError, quantizar


class StatusOS(Enum):
    RECEBIDA = "Recebida"
    EM_DIAGNOSTICO = "Em diagnóstico"
    AGUARDANDO_APROVACAO = "Aguardando aprovação"
    EM_EXECUCAO = "Em execução"
    FINALIZADA = "Finalizada"
    ENTREGUE = "Entregue"

    @property
    def descricao(self) -> str:
        return self.value

    def proximos_permitidos(self) -> frozenset["StatusOS"]:
        return _TRANSICOES[self]

    def pode_transicionar_para(self, destino: "StatusOS") -> bool:
        return destino in self.proximos_permitidos()


_TRANSICOES: dict[StatusOS, frozenset[StatusOS]] = {
    StatusOS.RECEBIDA: frozenset({StatusOS.EM_DIAGNOSTICO}),
    StatusOS.EM_DIAGNOSTICO: frozenset({StatusOS.AGUARDANDO_APROVACAO}),
    # aprovado -> execução; rejeitado -> finalizada sem execução (veículo devolvido ao cliente)
    StatusOS.AGUARDANDO_APROVACAO: frozenset({StatusOS.EM_EXECUCAO, StatusOS.FINALIZADA}),
    StatusOS.EM_EXECUCAO: frozenset({StatusOS.FINALIZADA}),
    StatusOS.FINALIZADA: frozenset({StatusOS.ENTREGUE}),
    StatusOS.ENTREGUE: frozenset(),
}


class OrcamentoStatus(Enum):
    NAO_GERADO = "NAO_GERADO"
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    REJEITADO = "REJEITADO"


@dataclass(frozen=True)
class ItemServico:
    """Serviço incluído na OS, com o preço "congelado" no momento da inclusão."""

    servico_id: int | None
    nome_servico: str
    preco: Decimal


@dataclass(frozen=True)
class ItemPeca:
    """Peça/insumo incluído na OS, com o preço "congelado" no momento da inclusão."""

    peca_id: int | None
    nome_peca: str
    preco_unitario: Decimal
    quantidade: int

    @property
    def subtotal(self) -> Decimal:
        return quantizar(self.preco_unitario * self.quantidade)


def _agora(agora: datetime | None) -> datetime:
    return agora if agora is not None else datetime.now(timezone.utc)


@dataclass
class OrdemServico:
    cliente_id: int
    veiculo_id: int
    codigo_acompanhamento: str
    status: StatusOS
    orcamento_status: OrcamentoStatus
    criada_em: datetime
    servicos: list[ItemServico] = field(default_factory=list)
    pecas: list[ItemPeca] = field(default_factory=list)
    inicio_execucao_em: datetime | None = None
    fim_execucao_em: datetime | None = None
    entregue_em: datetime | None = None
    id: int | None = None

    # ---------- criação ----------

    @classmethod
    def abrir(cls, cliente_id: int, veiculo_id: int, agora: datetime | None = None) -> "OrdemServico":
        if cliente_id is None or veiculo_id is None:
            raise RegraNegocioError("Cliente e veículo são obrigatórios para abrir uma ordem de serviço")
        return cls(
            cliente_id=cliente_id,
            veiculo_id=veiculo_id,
            codigo_acompanhamento=str(uuid.uuid4()),
            status=StatusOS.RECEBIDA,
            orcamento_status=OrcamentoStatus.NAO_GERADO,
            criada_em=_agora(agora),
        )

    # ---------- itens ----------

    def adicionar_servico(self, servico: Servico) -> None:
        self._exigir_edicao_permitida()
        if servico is None:
            raise RegraNegocioError("Serviço é obrigatório")
        self.servicos.append(ItemServico(servico.id, servico.nome, servico.preco))

    def adicionar_peca(self, peca: Peca, quantidade: int) -> None:
        self._exigir_edicao_permitida()
        if peca is None:
            raise RegraNegocioError("Peça é obrigatória")
        if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade <= 0:
            raise RegraNegocioError("Quantidade da peça deve ser maior que zero")
        self.pecas.append(ItemPeca(peca.id, peca.nome, peca.preco, quantidade))

    def _exigir_edicao_permitida(self) -> None:
        if self.status not in (StatusOS.RECEBIDA, StatusOS.EM_DIAGNOSTICO):
            raise RegraNegocioError("Itens só podem ser alterados nos status Recebida ou Em diagnóstico")

    # ---------- orçamento ----------

    @property
    def valor_servicos(self) -> Decimal:
        return quantizar(sum((i.preco for i in self.servicos), Decimal("0")))

    @property
    def valor_pecas(self) -> Decimal:
        return quantizar(sum((i.subtotal for i in self.pecas), Decimal("0")))

    @property
    def valor_total(self) -> Decimal:
        return quantizar(self.valor_servicos + self.valor_pecas)

    # ---------- transições de status ----------

    def iniciar_diagnostico(self) -> None:
        self._transicionar_para(StatusOS.EM_DIAGNOSTICO)

    def enviar_orcamento(self) -> None:
        """Gera o orçamento a partir dos itens e o disponibiliza ao cliente para aprovação."""
        if self.status == StatusOS.EM_DIAGNOSTICO and not self.servicos and not self.pecas:
            raise RegraNegocioError("Inclua ao menos um serviço ou peça antes de gerar o orçamento")
        self._transicionar_para(StatusOS.AGUARDANDO_APROVACAO)
        self.orcamento_status = OrcamentoStatus.PENDENTE

    def aprovar_orcamento(self, agora: datetime | None = None) -> None:
        self._exigir_orcamento_pendente()
        self._transicionar_para(StatusOS.EM_EXECUCAO)
        self.orcamento_status = OrcamentoStatus.APROVADO
        self.inicio_execucao_em = _agora(agora)

    def rejeitar_orcamento(self) -> None:
        """Rejeição encerra a OS sem execução; o veículo pode ser entregue ao cliente."""
        self._exigir_orcamento_pendente()
        self._transicionar_para(StatusOS.FINALIZADA)
        self.orcamento_status = OrcamentoStatus.REJEITADO

    def finalizar(self, agora: datetime | None = None) -> None:
        if self.status != StatusOS.EM_EXECUCAO:
            raise RegraNegocioError("Somente ordens em execução podem ser finalizadas")
        self._transicionar_para(StatusOS.FINALIZADA)
        self.fim_execucao_em = _agora(agora)

    def entregar(self, agora: datetime | None = None) -> None:
        self._transicionar_para(StatusOS.ENTREGUE)
        self.entregue_em = _agora(agora)

    def _exigir_orcamento_pendente(self) -> None:
        if self.status != StatusOS.AGUARDANDO_APROVACAO or self.orcamento_status != OrcamentoStatus.PENDENTE:
            raise RegraNegocioError("Não há orçamento pendente de aprovação para esta ordem de serviço")

    def _transicionar_para(self, destino: StatusOS) -> None:
        if not self.status.pode_transicionar_para(destino):
            raise RegraNegocioError(
                f"Transição inválida: de '{self.status.descricao}' para '{destino.descricao}'")
        self.status = destino

    def duracao_execucao(self) -> timedelta | None:
        """Tempo efetivo de execução (aprovação até finalização), se a OS passou por execução."""
        if self.inicio_execucao_em is None or self.fim_execucao_em is None:
            return None
        return self.fim_execucao_em - self.inicio_execucao_em
