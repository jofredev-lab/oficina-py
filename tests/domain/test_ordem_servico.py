import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.domain.ordem_servico import OrcamentoStatus, OrdemServico, StatusOS
from app.domain.peca import Peca
from app.domain.servico import Servico
from app.domain.shared import RegraNegocioError


class OrdemServicoTest(unittest.TestCase):
    def setUp(self):
        self.troca_oleo = Servico("Troca de óleo", "Óleo 5W30", Decimal("80.00"), id=1)
        self.filtro = Peca("FO-1", "Filtro de óleo", Decimal("25.50"), 10, 2, id=1)
        self.os = OrdemServico.abrir(cliente_id=1, veiculo_id=1)

    def _ate_aguardando_aprovacao(self):
        self.os.adicionar_servico(self.troca_oleo)
        self.os.iniciar_diagnostico()
        self.os.enviar_orcamento()

    def test_nova_os_nasce_recebida_sem_orcamento_e_com_codigo(self):
        self.assertEqual(StatusOS.RECEBIDA, self.os.status)
        self.assertEqual(OrcamentoStatus.NAO_GERADO, self.os.orcamento_status)
        self.assertEqual(36, len(self.os.codigo_acompanhamento))
        self.assertIsNotNone(self.os.criada_em)

    def test_exige_cliente_e_veiculo(self):
        with self.assertRaises(RegraNegocioError):
            OrdemServico.abrir(None, 1)
        with self.assertRaises(RegraNegocioError):
            OrdemServico.abrir(1, None)

    def test_calcula_orcamento_com_servicos_e_pecas(self):
        self.os.adicionar_servico(self.troca_oleo)
        self.os.adicionar_peca(self.filtro, 2)
        self.assertEqual(Decimal("80.00"), self.os.valor_servicos)
        self.assertEqual(Decimal("51.00"), self.os.valor_pecas)
        self.assertEqual(Decimal("131.00"), self.os.valor_total)
        self.assertEqual("Filtro de óleo", self.os.pecas[0].nome_peca)
        self.assertEqual("Troca de óleo", self.os.servicos[0].nome_servico)

    def test_preco_do_item_fica_congelado_no_momento_da_inclusao(self):
        self.os.adicionar_servico(self.troca_oleo)
        self.os.adicionar_peca(self.filtro, 1)
        self.troca_oleo.atualizar("Troca de óleo", None, 999)
        self.filtro.atualizar("FO-1", "Filtro", 999, 10, 2)
        self.assertEqual(Decimal("105.50"), self.os.valor_total)

    def test_valida_itens_adicionados(self):
        with self.assertRaises(RegraNegocioError):
            self.os.adicionar_servico(None)
        with self.assertRaises(RegraNegocioError):
            self.os.adicionar_peca(None, 1)
        with self.assertRaises(RegraNegocioError):
            self.os.adicionar_peca(self.filtro, 0)

    def test_fluxo_completo_ate_entrega(self):
        self.os.adicionar_servico(self.troca_oleo)
        self.os.adicionar_peca(self.filtro, 2)

        self.os.iniciar_diagnostico()
        self.assertEqual(StatusOS.EM_DIAGNOSTICO, self.os.status)

        self.os.enviar_orcamento()
        self.assertEqual(StatusOS.AGUARDANDO_APROVACAO, self.os.status)
        self.assertEqual(OrcamentoStatus.PENDENTE, self.os.orcamento_status)

        inicio = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)
        self.os.aprovar_orcamento(inicio)
        self.assertEqual(StatusOS.EM_EXECUCAO, self.os.status)
        self.assertEqual(OrcamentoStatus.APROVADO, self.os.orcamento_status)
        self.assertEqual(inicio, self.os.inicio_execucao_em)
        self.assertIsNone(self.os.duracao_execucao())

        self.os.finalizar(inicio + timedelta(minutes=90))
        self.assertEqual(StatusOS.FINALIZADA, self.os.status)
        self.assertEqual(timedelta(minutes=90), self.os.duracao_execucao())

        self.os.entregar()
        self.assertEqual(StatusOS.ENTREGUE, self.os.status)
        self.assertIsNotNone(self.os.entregue_em)

    def test_aprovacao_sem_instante_explicito_registra_inicio_da_execucao(self):
        self._ate_aguardando_aprovacao()
        self.os.aprovar_orcamento()
        self.assertIsNotNone(self.os.inicio_execucao_em)
        self.os.finalizar()
        self.assertIsNotNone(self.os.fim_execucao_em)
        self.assertIsNotNone(self.os.duracao_execucao())

    def test_rejeicao_finaliza_sem_execucao_e_nao_gera_duracao(self):
        self._ate_aguardando_aprovacao()
        self.os.rejeitar_orcamento()
        self.assertEqual(StatusOS.FINALIZADA, self.os.status)
        self.assertEqual(OrcamentoStatus.REJEITADO, self.os.orcamento_status)
        self.assertIsNone(self.os.duracao_execucao())
        self.os.entregar()
        self.assertEqual(StatusOS.ENTREGUE, self.os.status)

    def test_nao_gera_orcamento_sem_itens(self):
        self.os.iniciar_diagnostico()
        with self.assertRaisesRegex(RegraNegocioError, "ao menos um serviço ou peça"):
            self.os.enviar_orcamento()
        self.assertEqual(StatusOS.EM_DIAGNOSTICO, self.os.status)

    def test_nao_permite_pular_etapas(self):
        self.os.adicionar_servico(self.troca_oleo)
        for acao in (self.os.enviar_orcamento, self.os.aprovar_orcamento, self.os.rejeitar_orcamento,
                     self.os.finalizar, self.os.entregar):
            with self.subTest(acao=acao.__name__):
                with self.assertRaises(RegraNegocioError):
                    acao()
        self.os.iniciar_diagnostico()
        with self.assertRaises(RegraNegocioError):
            self.os.iniciar_diagnostico()
        with self.assertRaises(RegraNegocioError):
            self.os.aprovar_orcamento()
        self.os.enviar_orcamento()
        with self.assertRaises(RegraNegocioError):
            self.os.finalizar()
        with self.assertRaises(RegraNegocioError):
            self.os.entregar()

    def test_nao_permite_alterar_itens_depois_do_envio_do_orcamento(self):
        self._ate_aguardando_aprovacao()
        with self.assertRaises(RegraNegocioError):
            self.os.adicionar_servico(self.troca_oleo)
        with self.assertRaises(RegraNegocioError):
            self.os.adicionar_peca(self.filtro, 1)

    def test_nao_permite_aprovar_duas_vezes(self):
        self._ate_aguardando_aprovacao()
        self.os.aprovar_orcamento()
        with self.assertRaises(RegraNegocioError):
            self.os.aprovar_orcamento()
        with self.assertRaises(RegraNegocioError):
            self.os.rejeitar_orcamento()

    def test_regras_de_transicao_do_status(self):
        self.assertEqual(1, len(StatusOS.RECEBIDA.proximos_permitidos()))
        self.assertTrue(StatusOS.AGUARDANDO_APROVACAO.pode_transicionar_para(StatusOS.EM_EXECUCAO))
        self.assertTrue(StatusOS.AGUARDANDO_APROVACAO.pode_transicionar_para(StatusOS.FINALIZADA))
        self.assertEqual(frozenset(), StatusOS.ENTREGUE.proximos_permitidos())
        self.assertEqual("Em diagnóstico", StatusOS.EM_DIAGNOSTICO.descricao)
        for status in StatusOS:
            with self.subTest(status=status):
                self.assertFalse(status.pode_transicionar_para(status))


if __name__ == "__main__":
    unittest.main()
