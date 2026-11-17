import unittest
from decimal import Decimal

from app.domain.cliente import Cliente, Documento
from app.domain.peca import Peca
from app.domain.servico import Servico
from app.domain.shared import RegraNegocioError, quantizar
from app.domain.veiculo import Placa, Veiculo


class CadastrosTest(unittest.TestCase):
    cpf = Documento.of("529.982.247-25")

    def test_cliente_valida_campos_obrigatorios(self):
        with self.assertRaises(RegraNegocioError):
            Cliente(" ", self.cpf)
        with self.assertRaises(RegraNegocioError):
            Cliente("João", None)
        c = Cliente("  João  ", self.cpf, "joao@email.com", "61999999999")
        self.assertEqual("João", c.nome)
        self.assertEqual("joao@email.com", c.email)
        self.assertEqual("61999999999", c.telefone)
        c.atualizar("João da Silva", self.cpf)
        self.assertEqual("João da Silva", c.nome)

    def test_veiculo_valida_campos_obrigatorios(self):
        placa = Placa.of("ABC1D23")
        with self.assertRaises(RegraNegocioError):
            Veiculo(None, "Fiat", "Uno", 2015, 1)
        with self.assertRaises(RegraNegocioError):
            Veiculo(placa, " ", "Uno", 2015, 1)
        with self.assertRaises(RegraNegocioError):
            Veiculo(placa, "Fiat", "", 2015, 1)
        with self.assertRaises(RegraNegocioError):
            Veiculo(placa, "Fiat", "Uno", 1800, 1)
        with self.assertRaises(RegraNegocioError):
            Veiculo(placa, "Fiat", "Uno", None, 1)
        with self.assertRaises(RegraNegocioError):
            Veiculo(placa, "Fiat", "Uno", True, 1)
        with self.assertRaises(RegraNegocioError):
            Veiculo(placa, "Fiat", "Uno", 2015, None)
        v = Veiculo(placa, "Fiat", "Uno", 2015, 1)
        self.assertEqual(("Fiat", "Uno", 2015, 1), (v.marca, v.modelo, v.ano, v.cliente_id))
        v.atualizar(Placa.of("DEF4567"), "VW", "Gol", 2020, 2)
        self.assertEqual("Gol", v.modelo)
        self.assertEqual(2, v.cliente_id)

    def test_servico_valida_campos_obrigatorios(self):
        with self.assertRaises(RegraNegocioError):
            Servico("", "d", 1)
        with self.assertRaises(RegraNegocioError):
            Servico("Troca", "d", Decimal("-1"))
        with self.assertRaises(RegraNegocioError):
            Servico("Troca", "d", None)
        s = Servico("Troca de óleo", "desc", 80)
        self.assertEqual(Decimal("80.00"), s.preco)
        s.atualizar("Alinhamento", "novo", 120.5)
        self.assertEqual("Alinhamento", s.nome)
        self.assertEqual(Decimal("120.50"), s.preco)

    def test_peca_valida_campos_obrigatorios(self):
        with self.assertRaises(RegraNegocioError):
            Peca(" ", "Filtro", 1, 1, 1)
        with self.assertRaises(RegraNegocioError):
            Peca("F1", "", 1, 1, 1)
        with self.assertRaises(RegraNegocioError):
            Peca("F1", "Filtro", -2, 1, 1)
        with self.assertRaises(RegraNegocioError):
            Peca("F1", "Filtro", None, 1, 1)
        with self.assertRaises(RegraNegocioError):
            Peca("F1", "Filtro", 1, -1, 1)
        with self.assertRaises(RegraNegocioError):
            Peca("F1", "Filtro", 1, 1, -1)
        p = Peca(" f1 ", "Filtro", Decimal("25.5"), 10, 2)
        self.assertEqual("F1", p.codigo)
        self.assertEqual(Decimal("25.50"), p.preco)
        self.assertEqual(2, p.estoque_minimo)
        p.atualizar("F2", "Filtro de ar", 10, 4, 1)
        self.assertEqual("F2", p.codigo)
        self.assertEqual(4, p.quantidade_estoque)

    def test_controle_de_estoque(self):
        p = Peca("F1", "Filtro", 10, 10, 3)
        p.baixar_estoque(4)
        self.assertEqual(6, p.quantidade_estoque)
        self.assertFalse(p.estoque_baixo)
        p.baixar_estoque(3)
        self.assertTrue(p.estoque_baixo)
        p.repor_estoque(10)
        self.assertEqual(13, p.quantidade_estoque)
        self.assertFalse(p.estoque_baixo)

    def test_nao_permite_baixa_acima_do_estoque_nem_quantidade_invalida(self):
        p = Peca("F1", "Filtro", 10, 2, 1)
        with self.assertRaisesRegex(RegraNegocioError, "Estoque insuficiente"):
            p.baixar_estoque(3)
        self.assertEqual(2, p.quantidade_estoque)
        with self.assertRaises(RegraNegocioError):
            p.baixar_estoque(0)
        with self.assertRaises(RegraNegocioError):
            p.repor_estoque(-1)

    def test_quantizar_arredonda_para_duas_casas(self):
        self.assertEqual(Decimal("10.01"), quantizar("10.005"))
        self.assertEqual(Decimal("0.10"), quantizar(0.1))


if __name__ == "__main__":
    unittest.main()
