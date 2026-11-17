"""Testes de integração da API (rotas + casos de uso + persistência + JWT).

O mesmo conjunto roda contra a persistência em memória e contra SQLAlchemy/SQLite
(que exercita o mesmo código usado com PostgreSQL).
"""
from datetime import datetime, timedelta, timezone

import jwt as pyjwt

from app.config import Settings
from app.factory import create_app

SETTINGS = Settings()


class ApiTestBase:
    """Mixin com os testes; as subclasses informam como criar a persistência."""

    def make_uow_factory(self):  # pragma: no cover
        raise NotImplementedError

    def setUp(self):
        self.app = create_app(SETTINGS, uow_factory=self.make_uow_factory())
        self.client = self.app.test_client()
        self.token = self.login()

    # ---------- helpers ----------

    def login(self):
        resposta = self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(200, resposta.status_code)
        self.assertEqual("Bearer", resposta.get_json()["tipo"])
        return resposta.get_json()["token"]

    def auth(self):
        return {"Authorization": f"Bearer {self.token}"}

    def post(self, url, body=None, token=True):
        return self.client.post(url, json=body, headers=self.auth() if token else {})

    def get(self, url, token=True):
        return self.client.get(url, headers=self.auth() if token else {})

    def criar_cliente(self, documento="529.982.247-25", nome="João da Silva"):
        r = self.post("/api/admin/clientes", {"nome": nome, "documento": documento,
                                              "email": "cliente@email.com", "telefone": "61999999999"})
        self.assertEqual(201, r.status_code, r.get_data(as_text=True))
        return r.get_json()["id"]

    def criar_servico(self, nome="Troca de óleo", preco=80.00):
        r = self.post("/api/admin/servicos", {"nome": nome, "descricao": "descrição", "preco": preco})
        self.assertEqual(201, r.status_code)
        return r.get_json()["id"]

    def criar_peca(self, codigo="FO-100", preco=25.50, estoque=10):
        r = self.post("/api/admin/pecas", {"codigo": codigo, "nome": f"Peça {codigo}", "preco": preco,
                                           "quantidadeEstoque": estoque, "estoqueMinimo": 1})
        self.assertEqual(201, r.status_code)
        return r.get_json()["id"]

    def abrir_os(self, documento, placa, servico_id, peca_id, quantidade):
        r = self.post("/api/admin/ordens-servico", {
            "documentoCliente": documento,
            "veiculo": {"placa": placa, "marca": "Fiat", "modelo": "Uno", "ano": 2018},
            "servicosIds": [servico_id],
            "pecas": [{"pecaId": peca_id, "quantidade": quantidade}]})
        self.assertEqual(201, r.status_code, r.get_data(as_text=True))
        return r.get_json()

    def preparar_os_aguardando_aprovacao(self, documento, placa, estoque, quantidade, codigo_peca):
        self.criar_cliente(documento)
        servico_id = self.criar_servico()
        peca_id = self.criar_peca(codigo_peca, 10.00, estoque)
        os_ = self.abrir_os(documento, placa, servico_id, peca_id, quantidade)
        self.assertEqual(200, self.post(f"/api/admin/ordens-servico/{os_['id']}/diagnostico").status_code)
        self.assertEqual(200, self.post(f"/api/admin/ordens-servico/{os_['id']}/orcamento/enviar").status_code)
        return os_, peca_id

    # ---------- fluxos principais ----------

    def test_fluxo_completo_da_criacao_ate_a_entrega_com_aprovacao_do_cliente(self):
        cpf = "529.982.247-25"
        self.criar_cliente(cpf)
        servico_id = self.criar_servico()
        peca_id = self.criar_peca("FO-100", 25.50, 10)

        os_ = self.abrir_os(cpf, "ABC1D23", servico_id, peca_id, 2)
        os_id, codigo = os_["id"], os_["codigoAcompanhamento"]
        self.assertEqual("RECEBIDA", os_["status"])
        self.assertEqual("NAO_GERADO", os_["orcamentoStatus"])
        self.assertEqual(131.0, os_["valorTotal"])
        self.assertEqual("ABC1D23", os_["veiculoPlaca"])

        r = self.post(f"/api/admin/ordens-servico/{os_id}/diagnostico")
        self.assertEqual("EM_DIAGNOSTICO", r.get_json()["status"])

        r = self.post(f"/api/admin/ordens-servico/{os_id}/orcamento/enviar")
        self.assertEqual("AGUARDANDO_APROVACAO", r.get_json()["status"])
        self.assertEqual("PENDENTE", r.get_json()["orcamentoStatus"])

        # cliente consulta o andamento pela API pública (sem JWT)
        r = self.get(f"/api/public/acompanhamento/{codigo}", token=False)
        self.assertEqual(200, r.status_code)
        self.assertEqual("AGUARDANDO_APROVACAO", r.get_json()["status"])
        self.assertEqual(131.0, r.get_json()["valorTotal"])
        self.assertNotIn("clienteNome", r.get_json())

        # cliente aprova: inicia execução e baixa estoque
        r = self.post(f"/api/public/acompanhamento/{codigo}/orcamento/aprovar", token=False)
        self.assertEqual(200, r.status_code)
        self.assertEqual("EM_EXECUCAO", r.get_json()["status"])
        self.assertEqual("APROVADO", r.get_json()["orcamentoStatus"])
        self.assertEqual(8, self.get(f"/api/admin/pecas/{peca_id}").get_json()["quantidadeEstoque"])

        r = self.post(f"/api/admin/ordens-servico/{os_id}/finalizar")
        self.assertEqual("FINALIZADA", r.get_json()["status"])
        r = self.post(f"/api/admin/ordens-servico/{os_id}/entregar")
        self.assertEqual("ENTREGUE", r.get_json()["status"])

        r = self.get(f"/api/admin/ordens-servico/{os_id}")
        corpo = r.get_json()
        self.assertEqual("ENTREGUE", corpo["status"])
        self.assertEqual(1, len(corpo["servicos"]))
        self.assertEqual(1, len(corpo["pecas"]))
        self.assertIsNotNone(corpo["inicioExecucaoEm"])
        self.assertIsNotNone(corpo["entregueEm"])

        r = self.get("/api/admin/ordens-servico?status=ENTREGUE")
        self.assertEqual(1, len(r.get_json()))
        self.assertEqual([], self.get("/api/admin/ordens-servico?status=RECEBIDA").get_json())

        metricas = self.get("/api/admin/metricas/tempo-medio-execucao").get_json()
        self.assertGreaterEqual(metricas["quantidadeOrdens"], 1)

    def test_aprovacao_com_estoque_insuficiente_faz_rollback(self):
        os_, peca_id = self.preparar_os_aguardando_aprovacao(
            "11.222.333/0001-81", "DEF4567", estoque=1, quantidade=5, codigo_peca="PA-200")
        codigo = os_["codigoAcompanhamento"]

        r = self.post(f"/api/public/acompanhamento/{codigo}/orcamento/aprovar", token=False)
        self.assertEqual(422, r.status_code)
        self.assertIn("Estoque insuficiente", r.get_json()["detail"])

        # transação revertida: status e estoque não mudaram
        corpo = self.get(f"/api/admin/ordens-servico/{os_['id']}").get_json()
        self.assertEqual("AGUARDANDO_APROVACAO", corpo["status"])
        self.assertEqual("PENDENTE", corpo["orcamentoStatus"])
        self.assertEqual(1, self.get(f"/api/admin/pecas/{peca_id}").get_json()["quantidadeEstoque"])

    def test_rollback_parcial_quando_a_segunda_peca_nao_tem_estoque(self):
        cpf = "529.982.247-25"
        self.criar_cliente(cpf)
        servico_id = self.criar_servico()
        peca_a = self.criar_peca("PA-1", 10.00, 10)
        peca_b = self.criar_peca("PB-1", 10.00, 1)
        r = self.post("/api/admin/ordens-servico", {
            "documentoCliente": cpf,
            "veiculo": {"placa": "ABC1D23", "marca": "Fiat", "modelo": "Uno", "ano": 2018},
            "servicosIds": [servico_id],
            "pecas": [{"pecaId": peca_a, "quantidade": 3}, {"pecaId": peca_b, "quantidade": 5}]})
        os_id = r.get_json()["id"]
        self.post(f"/api/admin/ordens-servico/{os_id}/diagnostico")
        self.post(f"/api/admin/ordens-servico/{os_id}/orcamento/enviar")

        self.assertEqual(422, self.post(f"/api/admin/ordens-servico/{os_id}/orcamento/aprovar").status_code)
        # a baixa da primeira peça também foi desfeita
        self.assertEqual(10, self.get(f"/api/admin/pecas/{peca_a}").get_json()["quantidadeEstoque"])
        self.assertEqual("AGUARDANDO_APROVACAO", self.get(f"/api/admin/ordens-servico/{os_id}").get_json()["status"])

    def test_cliente_pode_rejeitar_orcamento_e_a_os_e_finalizada_sem_execucao(self):
        os_, peca_id = self.preparar_os_aguardando_aprovacao(
            "111.444.777-35", "GHI1J23", estoque=5, quantidade=1, codigo_peca="PR-300")
        r = self.post(f"/api/public/acompanhamento/{os_['codigoAcompanhamento']}/orcamento/rejeitar", token=False)
        self.assertEqual(200, r.status_code)
        self.assertEqual("FINALIZADA", r.get_json()["status"])
        self.assertEqual("REJEITADO", r.get_json()["orcamentoStatus"])
        self.assertEqual(5, self.get(f"/api/admin/pecas/{peca_id}").get_json()["quantidadeEstoque"])
        self.assertEqual("ENTREGUE", self.post(f"/api/admin/ordens-servico/{os_['id']}/entregar").get_json()["status"])

    def test_aprovacao_e_rejeicao_pelo_balcao(self):
        os_, peca_id = self.preparar_os_aguardando_aprovacao(
            "529.982.247-25", "JKL4M56", estoque=5, quantidade=2, codigo_peca="PB-400")
        r = self.post(f"/api/admin/ordens-servico/{os_['id']}/orcamento/aprovar")
        self.assertEqual("EM_EXECUCAO", r.get_json()["status"])
        self.assertEqual(3, self.get(f"/api/admin/pecas/{peca_id}").get_json()["quantidadeEstoque"])

        os2, _ = self.preparar_os_aguardando_aprovacao(
            "11.222.333/0001-81", "MNO5P67", estoque=5, quantidade=1, codigo_peca="PB-401")
        r = self.post(f"/api/admin/ordens-servico/{os2['id']}/orcamento/rejeitar")
        self.assertEqual("REJEITADO", r.get_json()["orcamentoStatus"])

    def test_nao_permite_pular_status(self):
        cpf = "529.982.247-25"
        self.criar_cliente(cpf)
        os_ = self.abrir_os(cpf, "JKL4M56", self.criar_servico(), self.criar_peca("PP-400", 40.0, 4), 1)
        self.assertEqual(422, self.post(f"/api/admin/ordens-servico/{os_['id']}/finalizar").status_code)
        self.assertEqual(422, self.post(f"/api/admin/ordens-servico/{os_['id']}/orcamento/enviar").status_code)

    def test_adicionar_itens_so_antes_do_envio_do_orcamento(self):
        cpf = "529.982.247-25"
        self.criar_cliente(cpf)
        servico_id = self.criar_servico()
        peca_id = self.criar_peca("PI-500", 10.0, 5)
        os_ = self.abrir_os(cpf, "ABC1D23", servico_id, peca_id, 1)
        r = self.post(f"/api/admin/ordens-servico/{os_['id']}/itens",
                      {"servicosIds": [servico_id], "pecas": [{"pecaId": peca_id, "quantidade": 2}]})
        self.assertEqual(200, r.status_code)
        self.assertEqual(2, len(r.get_json()["servicos"]))
        self.assertEqual(2, len(r.get_json()["pecas"]))
        self.assertEqual(80.0 * 2 + 10.0 * 3, r.get_json()["valorTotal"])
        self.post(f"/api/admin/ordens-servico/{os_['id']}/diagnostico")
        self.post(f"/api/admin/ordens-servico/{os_['id']}/orcamento/enviar")
        r = self.post(f"/api/admin/ordens-servico/{os_['id']}/itens", {"servicosIds": [servico_id]})
        self.assertEqual(422, r.status_code)

    def test_reaproveita_veiculo_do_mesmo_cliente_e_recusa_de_outro(self):
        a = self.criar_cliente("529.982.247-25", "Cliente A")
        self.criar_cliente("111.444.777-35", "Cliente B")
        servico_id = self.criar_servico()
        peca_id = self.criar_peca("PV-600", 10.0, 50)
        self.abrir_os("529.982.247-25", "ABC1D23", servico_id, peca_id, 1)
        self.abrir_os("529.982.247-25", "abc-1d23", servico_id, peca_id, 1)  # mesma placa, mesmo cliente
        self.assertEqual(1, len(self.get(f"/api/admin/veiculos?clienteId={a}").get_json()))
        r = self.post("/api/admin/ordens-servico", {
            "documentoCliente": "111.444.777-35",
            "veiculo": {"placa": "ABC1D23", "marca": "Fiat", "modelo": "Uno", "ano": 2018}})
        self.assertEqual(422, r.status_code)

    def test_abertura_com_cliente_inexistente_retorna_404(self):
        r = self.post("/api/admin/ordens-servico", {
            "documentoCliente": "529.982.247-25",
            "veiculo": {"placa": "ABC1D23", "marca": "Fiat", "modelo": "Uno", "ano": 2018}})
        self.assertEqual(404, r.status_code)

    def test_abertura_com_servico_ou_peca_inexistente_retorna_404(self):
        self.criar_cliente("529.982.247-25")
        veiculo = {"placa": "ABC1D23", "marca": "Fiat", "modelo": "Uno", "ano": 2018}
        r = self.post("/api/admin/ordens-servico", {
            "documentoCliente": "529.982.247-25", "veiculo": veiculo, "servicosIds": [999]})
        self.assertEqual(404, r.status_code)
        r = self.post("/api/admin/ordens-servico", {
            "documentoCliente": "529.982.247-25", "veiculo": veiculo,
            "pecas": [{"pecaId": 999, "quantidade": 1}]})
        self.assertEqual(404, r.status_code)

    # ---------- validações ----------

    def test_rejeita_cpf_invalido_com_regra_de_negocio(self):
        r = self.post("/api/admin/clientes", {"nome": "Fulano", "documento": "111.111.111-11"})
        self.assertEqual(422, r.status_code)
        self.assertEqual("CPF inválido", r.get_json()["detail"])
        self.assertEqual("application/problem+json", r.mimetype)

    def test_rejeita_placa_invalida_na_abertura_da_os(self):
        self.criar_cliente("529.982.247-25")
        r = self.post("/api/admin/ordens-servico", {
            "documentoCliente": "529.982.247-25",
            "veiculo": {"placa": "PLACA-INVALIDA", "marca": "Fiat", "modelo": "Uno", "ano": 2018}})
        self.assertEqual(422, r.status_code)

    def test_valida_campos_obrigatorios_do_payload(self):
        r = self.post("/api/admin/clientes", {"nome": ""})
        self.assertEqual(400, r.status_code)
        self.assertIn("nome", r.get_json()["erros"])
        self.assertIn("documento", r.get_json()["erros"])

    def test_valida_tipos_e_itens_aninhados(self):
        r = self.post("/api/admin/ordens-servico", {
            "documentoCliente": "529.982.247-25",
            "veiculo": {"placa": "ABC1D23", "marca": "Fiat", "modelo": "Uno", "ano": "2018"},
            "servicosIds": ["a"],
            "pecas": [{"pecaId": 1, "quantidade": 0}, "x"]})
        self.assertEqual(400, r.status_code)
        erros = r.get_json()["erros"]
        self.assertIn("veiculo.ano", erros)
        self.assertIn("servicosIds[0]", erros)
        self.assertIn("pecas[0].quantidade", erros)
        self.assertIn("pecas[1]", erros)

    def test_corpo_ausente_ou_invalido_retorna_400(self):
        r = self.client.post("/api/admin/clientes", data="nao-e-json", headers=self.auth(),
                             content_type="application/json")
        self.assertEqual(400, r.status_code)
        self.assertEqual(400, self.post("/api/admin/clientes", None).status_code)

    def test_filtros_invalidos_retornam_400(self):
        self.assertEqual(400, self.get("/api/admin/ordens-servico?status=XPTO").status_code)
        self.assertEqual(400, self.get("/api/admin/veiculos?clienteId=abc").status_code)

    def test_duplicidade_de_cpf_retorna_conflito(self):
        self.criar_cliente("390.533.447-05", "Primeiro")
        r = self.post("/api/admin/clientes", {"nome": "Segundo", "documento": "390.533.447-05"})
        self.assertEqual(409, r.status_code)

    # ---------- CRUDs ----------

    def test_crud_de_clientes(self):
        cid = self.criar_cliente("529.982.247-25")
        self.assertEqual(1, len(self.get("/api/admin/clientes").get_json()))
        self.assertEqual("CPF", self.get(f"/api/admin/clientes/{cid}").get_json()["tipoDocumento"])
        r = self.client.put(f"/api/admin/clientes/{cid}", headers=self.auth(),
                            json={"nome": "Novo Nome", "documento": "529.982.247-25"})
        self.assertEqual("Novo Nome", r.get_json()["nome"])
        outro = self.criar_cliente("111.444.777-35", "Outro")
        r = self.client.put(f"/api/admin/clientes/{outro}", headers=self.auth(),
                            json={"nome": "Outro", "documento": "529.982.247-25"})
        self.assertEqual(409, r.status_code)
        self.assertEqual(204, self.client.delete(f"/api/admin/clientes/{cid}", headers=self.auth()).status_code)
        self.assertEqual(404, self.get(f"/api/admin/clientes/{cid}").status_code)
        self.assertEqual(404, self.client.delete(f"/api/admin/clientes/{cid}", headers=self.auth()).status_code)

    def test_crud_de_veiculos(self):
        cid = self.criar_cliente()
        corpo = {"placa": "ABC1D23", "marca": "Fiat", "modelo": "Uno", "ano": 2015, "clienteId": cid}
        r = self.post("/api/admin/veiculos", corpo)
        self.assertEqual(201, r.status_code)
        vid = r.get_json()["id"]
        self.assertEqual(409, self.post("/api/admin/veiculos", corpo).status_code)
        self.assertEqual(404, self.post("/api/admin/veiculos", {**corpo, "placa": "DEF4567", "clienteId": 999}).status_code)
        r = self.client.put(f"/api/admin/veiculos/{vid}", headers=self.auth(), json={**corpo, "modelo": "Palio"})
        self.assertEqual("Palio", r.get_json()["modelo"])
        self.assertEqual("Palio", self.get(f"/api/admin/veiculos/{vid}").get_json()["modelo"])
        self.assertEqual(1, len(self.get("/api/admin/veiculos").get_json()))
        self.assertEqual(204, self.client.delete(f"/api/admin/veiculos/{vid}", headers=self.auth()).status_code)

    def test_crud_de_servicos(self):
        sid = self.criar_servico("Alinhamento", 120.5)
        self.assertEqual(120.5, self.get(f"/api/admin/servicos/{sid}").get_json()["preco"])
        r = self.client.put(f"/api/admin/servicos/{sid}", headers=self.auth(),
                            json={"nome": "Alinhamento 3D", "preco": 150})
        self.assertEqual("Alinhamento 3D", r.get_json()["nome"])
        self.assertEqual(1, len(self.get("/api/admin/servicos").get_json()))
        self.assertEqual(204, self.client.delete(f"/api/admin/servicos/{sid}", headers=self.auth()).status_code)

    def test_crud_e_controle_de_estoque_de_pecas(self):
        pid = self.criar_peca("FA-1", 30.0, 5)
        self.assertEqual(409, self.post("/api/admin/pecas", {
            "codigo": "fa-1", "nome": "Dup", "preco": 1, "quantidadeEstoque": 1, "estoqueMinimo": 0}).status_code)
        r = self.post(f"/api/admin/pecas/{pid}/estoque/entrada", {"quantidade": 5})
        self.assertEqual(10, r.get_json()["quantidadeEstoque"])
        r = self.post(f"/api/admin/pecas/{pid}/estoque/saida", {"quantidade": 9})
        self.assertEqual(1, r.get_json()["quantidadeEstoque"])
        self.assertTrue(r.get_json()["estoqueBaixo"])
        self.assertEqual(422, self.post(f"/api/admin/pecas/{pid}/estoque/saida", {"quantidade": 2}).status_code)
        self.assertEqual(400, self.post(f"/api/admin/pecas/{pid}/estoque/entrada", {"quantidade": 0}).status_code)
        self.assertEqual([pid], [p["id"] for p in self.get("/api/admin/pecas/estoque-baixo").get_json()])
        r = self.client.put(f"/api/admin/pecas/{pid}", headers=self.auth(), json={
            "codigo": "FA-1", "nome": "Filtro de ar", "preco": 35, "quantidadeEstoque": 20, "estoqueMinimo": 2})
        self.assertEqual(20, r.get_json()["quantidadeEstoque"])
        self.assertEqual([], self.get("/api/admin/pecas/estoque-baixo").get_json())
        outra = self.criar_peca("FA-2", 1.0, 1)
        r = self.client.put(f"/api/admin/pecas/{outra}", headers=self.auth(), json={
            "codigo": "FA-1", "nome": "x", "preco": 1, "quantidadeEstoque": 1, "estoqueMinimo": 0})
        self.assertEqual(409, r.status_code)
        self.assertEqual(2, len(self.get("/api/admin/pecas").get_json()))
        self.assertEqual(204, self.client.delete(f"/api/admin/pecas/{pid}", headers=self.auth()).status_code)

    def test_nao_remove_registros_em_uso(self):
        cpf = "529.982.247-25"
        cid = self.criar_cliente(cpf)
        servico_id = self.criar_servico()
        peca_id = self.criar_peca("PU-700", 10.0, 5)
        os_ = self.abrir_os(cpf, "ABC1D23", servico_id, peca_id, 1)
        veiculo_id = self.get(f"/api/admin/ordens-servico/{os_['id']}").get_json()["id"]
        veiculos = self.get(f"/api/admin/veiculos?clienteId={cid}").get_json()
        for url in (f"/api/admin/clientes/{cid}", f"/api/admin/veiculos/{veiculos[0]['id']}",
                    f"/api/admin/servicos/{servico_id}", f"/api/admin/pecas/{peca_id}"):
            with self.subTest(url=url):
                self.assertEqual(409, self.client.delete(url, headers=self.auth()).status_code)
        self.assertIsNotNone(veiculo_id)

    def test_tempo_medio_sem_dados(self):
        r = self.get("/api/admin/metricas/tempo-medio-execucao")
        self.assertEqual(0, r.get_json()["quantidadeOrdens"])
        self.assertEqual("sem dados", r.get_json()["tempoMedioFormatado"])

    # ---------- segurança ----------

    def test_apis_administrativas_exigem_jwt(self):
        self.assertEqual(401, self.get("/api/admin/clientes", token=False).status_code)
        self.assertEqual(401, self.client.get("/api/admin/ordens-servico",
                                              headers={"Authorization": "Bearer token.invalido.aqui"}).status_code)
        self.assertEqual(401, self.post("/api/admin/pecas", {"codigo": "X"}, token=False).status_code)
        self.assertEqual(401, self.client.get("/api/admin/clientes",
                                              headers={"Authorization": "Basic abc"}).status_code)

    def test_token_expirado_ou_assinado_com_outra_chave_e_recusado(self):
        agora = datetime.now(timezone.utc)
        expirado = pyjwt.encode({"sub": "admin", "exp": agora - timedelta(minutes=1)},
                                SETTINGS.jwt_secret, algorithm="HS256")
        falso = pyjwt.encode({"sub": "admin", "exp": agora + timedelta(minutes=5)},
                             "outra-chave-secreta-com-mais-de-32-caracteres!", algorithm="HS256")
        for token in (expirado, falso):
            r = self.client.get("/api/admin/clientes", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(401, r.status_code)

    def test_login_com_credenciais_invalidas_retorna_401(self):
        r = self.client.post("/api/auth/login", json={"username": "admin", "password": "senha-errada"})
        self.assertEqual(401, r.status_code)
        r = self.client.post("/api/auth/login", json={"username": "outro", "password": "admin123"})
        self.assertEqual(401, r.status_code)
        self.assertEqual(400, self.client.post("/api/auth/login", json={"username": "admin"}).status_code)

    def test_consulta_de_codigo_inexistente_retorna_404(self):
        self.assertEqual(404, self.get("/api/public/acompanhamento/codigo-inexistente", token=False).status_code)
        self.assertEqual(404, self.post("/api/public/acompanhamento/x/orcamento/aprovar", token=False).status_code)

    def test_rota_inexistente_retorna_problem_json(self):
        r = self.get("/api/nao-existe", token=False)
        self.assertEqual(404, r.status_code)
        self.assertEqual("application/problem+json", r.mimetype)

    # ---------- documentação ----------

    def test_openapi_e_swagger_estao_disponiveis_sem_autenticacao(self):
        r = self.get("/openapi.json", token=False)
        self.assertEqual(200, r.status_code)
        spec = r.get_json()
        self.assertEqual("3.0.3", spec["openapi"])
        for caminho in ("/api/auth/login", "/api/admin/clientes", "/api/admin/clientes/{id}",
                        "/api/admin/ordens-servico", "/api/admin/ordens-servico/{id}/orcamento/enviar",
                        "/api/public/acompanhamento/{codigo}", "/api/admin/metricas/tempo-medio-execucao"):
            self.assertIn(caminho, spec["paths"])
        self.assertEqual([{"bearerAuth": []}], spec["paths"]["/api/admin/clientes"]["post"]["security"])
        self.assertEqual([], spec["paths"]["/api/auth/login"]["post"]["security"])
        self.assertEqual(200, self.get("/swagger-ui", token=False).status_code)
        self.assertEqual(200, self.get("/swagger-ui.html", token=False).status_code)
        self.assertEqual("UP", self.get("/health", token=False).get_json()["status"])
