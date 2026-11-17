import time
import unittest

import jwt as pyjwt

from app.infrastructure.security.jwt_service import AuthService, CredenciaisInvalidasError, JwtService

SEGREDO = "segredo-de-teste-com-mais-de-32-caracteres!!"


class JwtServiceTest(unittest.TestCase):
    def test_exige_segredo_com_ao_menos_32_caracteres(self):
        with self.assertRaises(ValueError):
            JwtService("curto", 60)

    def test_gera_e_valida_token(self):
        service = JwtService(SEGREDO, 60)
        claims = service.validar(service.gerar("admin"))
        self.assertEqual("admin", claims["sub"])

    def test_token_expirado_e_invalido(self):
        service = JwtService(SEGREDO, -1)
        with self.assertRaises(pyjwt.InvalidTokenError):
            service.validar(service.gerar("admin"))

    def test_token_de_outra_chave_e_invalido(self):
        token = JwtService(SEGREDO, 60).gerar("admin")
        with self.assertRaises(pyjwt.InvalidTokenError):
            JwtService("outro-segredo-com-mais-de-32-caracteres!!!!", 60).validar(token)

    def test_autenticacao_do_administrador(self):
        auth = AuthService(JwtService(SEGREDO, 60), "admin", "senha-forte")
        token, expira_em = auth.autenticar("admin", "senha-forte")
        self.assertTrue(token)
        self.assertEqual(60, expira_em)
        for usuario, senha in (("admin", "errada"), ("outro", "senha-forte")):
            with self.assertRaises(CredenciaisInvalidasError):
                auth.autenticar(usuario, senha)


if __name__ == "__main__":
    unittest.main()
