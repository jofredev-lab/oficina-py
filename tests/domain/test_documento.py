import unittest

from app.domain.cliente import Documento, TipoDocumento
from app.domain.shared import RegraNegocioError


class DocumentoTest(unittest.TestCase):
    def test_aceita_cpf_valido_com_mascara_e_normaliza(self):
        d = Documento.of("529.982.247-25")
        self.assertEqual("52998224725", d.numero)
        self.assertEqual(TipoDocumento.CPF, d.tipo)

    def test_aceita_cnpj_valido_com_mascara(self):
        d = Documento.of("11.222.333/0001-81")
        self.assertEqual("11222333000181", d.numero)
        self.assertEqual(TipoDocumento.CNPJ, d.tipo)

    def test_rejeita_cpf_invalido(self):
        for cpf in ("529.982.247-24", "111.111.111-11", "000.000.000-00"):
            with self.subTest(cpf=cpf):
                with self.assertRaisesRegex(RegraNegocioError, "CPF inválido"):
                    Documento.of(cpf)

    def test_rejeita_cnpj_invalido(self):
        for cnpj in ("11.222.333/0001-82", "00.000.000/0000-00"):
            with self.subTest(cnpj=cnpj):
                with self.assertRaisesRegex(RegraNegocioError, "CNPJ inválido"):
                    Documento.of(cnpj)

    def test_rejeita_quantidade_de_digitos_invalida(self):
        for valor in ("123", "abc", "123456789012"):
            with self.subTest(valor=valor):
                with self.assertRaises(RegraNegocioError):
                    Documento.of(valor)

    def test_rejeita_nulo_ou_em_branco(self):
        with self.assertRaises(RegraNegocioError):
            Documento.of(None)
        with self.assertRaises(RegraNegocioError):
            Documento.of("   ")

    def test_construcao_direta_tambem_valida(self):
        with self.assertRaises(RegraNegocioError):
            Documento("5299822472a")

    def test_igualdade_por_valor(self):
        self.assertEqual(Documento.of("529.982.247-25"), Documento.of("52998224725"))
        self.assertEqual(hash(Documento.of("529.982.247-25")), hash(Documento.of("52998224725")))
        self.assertEqual("52998224725", str(Documento.of("529.982.247-25")))


if __name__ == "__main__":
    unittest.main()
