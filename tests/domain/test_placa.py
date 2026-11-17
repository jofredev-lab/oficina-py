import unittest

from app.domain.shared import RegraNegocioError
from app.domain.veiculo import Placa


class PlacaTest(unittest.TestCase):
    def test_aceita_padrao_antigo_com_hifen_e_normaliza(self):
        self.assertEqual("ABC1234", Placa.of("abc-1234").numero)

    def test_aceita_padrao_mercosul(self):
        self.assertEqual("ABC1D23", Placa.of("ABC1D23").numero)

    def test_rejeita_placa_invalida(self):
        for valor in ("AB12345", "ABCD123", "1234ABC", "ABC12", "ABC-12345"):
            with self.subTest(valor=valor):
                with self.assertRaises(RegraNegocioError):
                    Placa.of(valor)

    def test_rejeita_nulo_ou_em_branco(self):
        with self.assertRaises(RegraNegocioError):
            Placa.of(None)
        with self.assertRaises(RegraNegocioError):
            Placa.of(" ")

    def test_igualdade_por_valor(self):
        self.assertEqual(Placa.of("abc1d23"), Placa.of("ABC-1D23"))
        self.assertEqual("ABC1D23", str(Placa.of("abc1d23")))


if __name__ == "__main__":
    unittest.main()
