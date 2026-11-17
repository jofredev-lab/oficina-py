"""Casos de uso da Ordem de Serviço.

Cada método público é uma unidade de trabalho (transação): se qualquer regra falhar
(por exemplo, estoque insuficiente na aprovação), nada é persistido.
"""
from __future__ import annotations

from typing import Optional

from app.domain.cliente import Documento
from app.domain.ordem_servico import OrdemServico, StatusOS
from app.domain.shared import RecursoNaoEncontradoError, RegraNegocioError
from app.domain.veiculo import Placa, Veiculo

from .cadastros import UowFactory
from .commands import AbrirOrdemServicoDados, ItensDados, VeiculoOSDados
from .ports import UnitOfWork
from .views import OrdemServicoView, TempoMedioExecucao


class OrdemServicoService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow = uow_factory

    # ---------- criação ----------

    def abrir(self, dados: AbrirOrdemServicoDados) -> OrdemServicoView:
        documento = Documento.of(dados.documento_cliente)
        placa = Placa.of(dados.veiculo.placa)
        with self._uow() as uow:
            cliente = uow.clientes.get_by_documento(documento.numero)
            if cliente is None:
                raise RecursoNaoEncontradoError(
                    "Cliente não encontrado para o CPF/CNPJ informado. Cadastre o cliente antes de abrir a OS.")
            veiculo = self._obter_ou_cadastrar_veiculo(uow, cliente.id, placa, dados.veiculo)
            ordem = OrdemServico.abrir(cliente.id, veiculo.id)
            self._incluir_itens(uow, ordem, dados.itens)
            ordem = uow.ordens.save(ordem)
            return OrdemServicoView(ordem, cliente, veiculo)

    @staticmethod
    def _obter_ou_cadastrar_veiculo(uow: UnitOfWork, cliente_id: int, placa: Placa,
                                    dados: VeiculoOSDados) -> Veiculo:
        existente = uow.veiculos.get_by_placa(placa.numero)
        if existente is not None:
            if existente.cliente_id != cliente_id:
                raise RegraNegocioError(
                    f"O veículo de placa {placa.numero} está cadastrado para outro cliente")
            return existente
        return uow.veiculos.save(Veiculo(placa, dados.marca, dados.modelo, dados.ano, cliente_id))

    def adicionar_itens(self, id: int, itens: ItensDados) -> OrdemServicoView:
        with self._uow() as uow:
            ordem = self._obter(uow, id)
            self._incluir_itens(uow, ordem, itens)
            return self._salvar_e_montar(uow, ordem)

    @staticmethod
    def _incluir_itens(uow: UnitOfWork, ordem: OrdemServico, itens: ItensDados) -> None:
        for servico_id in itens.servicos_ids:
            servico = uow.servicos.get(servico_id)
            if servico is None:
                raise RecursoNaoEncontradoError(f"Serviço não encontrado: {servico_id}")
            ordem.adicionar_servico(servico)
        for item in itens.pecas:
            peca = uow.pecas.get(item.peca_id)
            if peca is None:
                raise RecursoNaoEncontradoError(f"Peça não encontrada: {item.peca_id}")
            ordem.adicionar_peca(peca, item.quantidade)

    # ---------- consultas administrativas ----------

    def listar(self, status: Optional[StatusOS] = None) -> list[OrdemServicoView]:
        with self._uow() as uow:
            return [self._montar(uow, o) for o in uow.ordens.list_all(status)]

    def buscar(self, id: int) -> OrdemServicoView:
        with self._uow() as uow:
            return self._montar(uow, self._obter(uow, id))

    # ---------- fluxo de status ----------

    def iniciar_diagnostico(self, id: int) -> OrdemServicoView:
        with self._uow() as uow:
            ordem = self._obter(uow, id)
            ordem.iniciar_diagnostico()
            return self._salvar_e_montar(uow, ordem)

    def enviar_orcamento(self, id: int) -> OrdemServicoView:
        with self._uow() as uow:
            ordem = self._obter(uow, id)
            ordem.enviar_orcamento()
            return self._salvar_e_montar(uow, ordem)

    def aprovar_orcamento(self, id: int) -> OrdemServicoView:
        with self._uow() as uow:
            ordem = self._obter(uow, id)
            self._aplicar_aprovacao(uow, ordem)
            return self._salvar_e_montar(uow, ordem)

    def rejeitar_orcamento(self, id: int) -> OrdemServicoView:
        with self._uow() as uow:
            ordem = self._obter(uow, id)
            ordem.rejeitar_orcamento()
            return self._salvar_e_montar(uow, ordem)

    def finalizar(self, id: int) -> OrdemServicoView:
        with self._uow() as uow:
            ordem = self._obter(uow, id)
            ordem.finalizar()
            return self._salvar_e_montar(uow, ordem)

    def entregar(self, id: int) -> OrdemServicoView:
        with self._uow() as uow:
            ordem = self._obter(uow, id)
            ordem.entregar()
            return self._salvar_e_montar(uow, ordem)

    @staticmethod
    def _aplicar_aprovacao(uow: UnitOfWork, ordem: OrdemServico) -> None:
        """Aprova o orçamento e baixa o estoque das peças na mesma transação (tudo ou nada)."""
        ordem.aprovar_orcamento()
        for item in ordem.pecas:
            peca = uow.pecas.get(item.peca_id)
            peca.baixar_estoque(item.quantidade)
            uow.pecas.save(peca)

    # ---------- acompanhamento pelo cliente ----------

    def consultar_acompanhamento(self, codigo: str) -> OrdemServicoView:
        with self._uow() as uow:
            return self._montar(uow, self._obter_por_codigo(uow, codigo))

    def aprovar_por_codigo(self, codigo: str) -> OrdemServicoView:
        with self._uow() as uow:
            ordem = self._obter_por_codigo(uow, codigo)
            self._aplicar_aprovacao(uow, ordem)
            return self._salvar_e_montar(uow, ordem)

    def rejeitar_por_codigo(self, codigo: str) -> OrdemServicoView:
        with self._uow() as uow:
            ordem = self._obter_por_codigo(uow, codigo)
            ordem.rejeitar_orcamento()
            return self._salvar_e_montar(uow, ordem)

    # ---------- métricas ----------

    def tempo_medio_execucao(self) -> TempoMedioExecucao:
        with self._uow() as uow:
            ordens = uow.ordens.list_executadas()
        duracoes = [d for d in (o.duracao_execucao() for o in ordens) if d is not None]
        if not duracoes:
            return TempoMedioExecucao(0, 0.0, "sem dados")
        media_segundos = sum(d.total_seconds() for d in duracoes) / len(duracoes)
        total = round(media_segundos)
        formatado = f"{total // 3600}h {(total % 3600) // 60}min"
        return TempoMedioExecucao(len(duracoes), media_segundos / 60.0, formatado)

    # ---------- helpers ----------

    @staticmethod
    def _obter(uow: UnitOfWork, id: int) -> OrdemServico:
        ordem = uow.ordens.get(id)
        if ordem is None:
            raise RecursoNaoEncontradoError(f"Ordem de serviço não encontrada: {id}")
        return ordem

    @staticmethod
    def _obter_por_codigo(uow: UnitOfWork, codigo: str) -> OrdemServico:
        ordem = uow.ordens.get_by_codigo(codigo)
        if ordem is None:
            raise RecursoNaoEncontradoError("Ordem de serviço não encontrada para o código informado")
        return ordem

    @staticmethod
    def _montar(uow: UnitOfWork, ordem: OrdemServico) -> OrdemServicoView:
        return OrdemServicoView(ordem, uow.clientes.get(ordem.cliente_id), uow.veiculos.get(ordem.veiculo_id))

    def _salvar_e_montar(self, uow: UnitOfWork, ordem: OrdemServico) -> OrdemServicoView:
        return self._montar(uow, uow.ordens.save(ordem))
