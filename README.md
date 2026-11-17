# Oficina Mecânica — Sistema Integrado de Atendimento e Execução de Serviços (MVP) · Python/Flask

Tech Challenge · Fase 1 · SOAT — Software Architecture (Pós Tech)

## 1. Objetivo do projeto
Primeira versão (MVP) do back-end de uma oficina mecânica de médio porte, substituindo anotações manuais e planilhas por um sistema que organiza **ordens de serviço (OS)**, **clientes**, **veículos**, **serviços** e **peças/insumos (com estoque)**, e que permite ao cliente acompanhar o andamento e aprovar orçamentos via API.

## 2. Descrição resumida da solução
- A OS é aberta identificando o cliente por **CPF/CNPJ**; o veículo é cadastrado (ou reaproveitado pela placa) e os serviços/peças são incluídos.
- O **orçamento é calculado automaticamente** (serviços + peças × quantidade) e enviado ao cliente (`Aguardando aprovação`).
- O cliente consulta e **aprova/rejeita** pela API pública, usando o *código de acompanhamento* (UUID) da OS.
- A **aprovação baixa o estoque** das peças na mesma transação (Unit of Work): se faltar estoque, nada é alterado (rollback).
- O status segue o fluxo **Recebida → Em diagnóstico → Aguardando aprovação → Em execução → Finalizada → Entregue**, com regras de transição no domínio.
- APIs administrativas protegidas por **JWT**; documentação em **Swagger/OpenAPI**.

### Regras de negócio relevantes
| Regra | Onde está |
|---|---|
| CPF/CNPJ e placa válidos (objetos de valor) | `Documento`, `Placa` |
| Transições de status permitidas | `StatusOS` + `OrdemServico` |
| Itens só podem ser alterados em *Recebida* e *Em diagnóstico* | `OrdemServico` |
| Não gera orçamento sem ao menos um serviço/peça | `OrdemServico.enviar_orcamento()` |
| Rejeição do orçamento → OS *Finalizada* sem execução (veículo pode ser entregue) | `OrdemServico.rejeitar_orcamento()` |
| Baixa de estoque na aprovação, tudo-ou-nada, com lock otimista | `OrdemServicoService`, `Peca`, `PecaModel.versao` |
| Preço dos itens "congelado" no momento da inclusão na OS | `ItemServico`, `ItemPeca` |
| Tempo médio de execução = aprovação → finalização | `OrdemServico.duracao_execucao()` |

## 3. Arquitetura utilizada
**Monolito em camadas** com organização por contexto de domínio e inversão de dependência (estilo hexagonal / DDD tático):

```
interfaces (Flask: rotas, validação, erros)
        ↓
application (casos de uso + portas: repositórios e Unit of Work)
        ↓
domain (agregados, objetos de valor, regras — Python puro)
        ↑ implementa as portas
infrastructure (SQLAlchemy/PostgreSQL, persistência em memória, JWT)
```

- **domain**: `OrdemServico` (+ `ItemServico`, `ItemPeca`), `Cliente`, `Veiculo`, `Servico`, `Peca`, objetos de valor `Documento` e `Placa`, `StatusOS`. **Não importa Flask nem SQLAlchemy.**
- **application**: serviços de caso de uso (cada método = uma transação) e as *portas* (`ports.py`).
- **infrastructure**: adaptadores SQLAlchemy (PostgreSQL) e em memória; segurança JWT.
- **interfaces**: blueprints Flask, validação de entrada, serializadores e tratamento de erros (RFC 7807).
- `app/factory.py` (`create_app`) é a raiz de composição; a persistência é injetada, o que permite rodar os testes de API sem banco.

Documentação DDD (Event Storming, linguagem ubíqua, diagramas): [`docs/ddd/`](docs/ddd/).

## 4. Tecnologias utilizadas
Python 3.12 · Flask 3 · SQLAlchemy 2 · PostgreSQL 16 (psycopg2) · PyJWT · gunicorn · OpenAPI 3 + Swagger UI · unittest/pytest + coverage · Docker / Docker Compose.

## 5. Decisão e justificativa do banco de dados
**PostgreSQL** (relacional):
- O domínio é fortemente relacional (cliente → veículo → OS → itens → peças) e exige **integridade referencial** e **unicidade** (CPF/CNPJ, placa, código da peça).
- A aprovação da OS altera OS e estoque no mesmo fluxo: precisamos de **transações ACID** (tudo ou nada) e de lock otimista (`version_id_col`) para evitar baixas concorrentes inconsistentes.
- Consultas de gestão (listagem por status, tempo médio) são naturalmente expressas em SQL.
- Um banco de documentos (ex.: MongoDB) facilitaria dados sem esquema, mas dificultaria as garantias transacionais entre agregados que o estoque exige. Banco maduro, open source e com imagem oficial leve para Docker.

Nos testes, a mesma suíte roda contra **SQLite em memória** (via SQLAlchemy) e contra a persistência em memória, sem dependência externa.

## 6. Pré-requisitos
- **Docker** e **Docker Compose** (execução completa), ou
- **Python 3.12+** e um PostgreSQL local (execução sem Docker).

## 7. Instruções para execução

### Com Docker (recomendado)
```bash
docker compose up --build
```
- API: http://localhost:8080
- Swagger UI: http://localhost:8080/swagger-ui

### Sem Docker
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# suba um PostgreSQL com banco/usuário/senha "oficina" (ou ajuste DATABASE_URL)
python wsgi.py                                         # ou: gunicorn -b 0.0.0.0:8080 wsgi:app
```

### Variáveis de ambiente (todas opcionais — há valores de demonstração)
| Variável | Padrão (demo) |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://oficina:oficina@localhost:5432/oficina` |
| `JWT_SECRET` | segredo de demonstração (mín. 32 caracteres) — **troque em produção** |
| `JWT_EXPIRATION_SECONDS` | `3600` |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | `admin` / `admin123` |

## 8. Autenticação e credenciais de demonstração
1. `POST /api/auth/login` com `{"username":"admin","password":"admin123"}` → retorna `token`.
2. Envie `Authorization: Bearer <token>` nas rotas `/api/admin/**`.
3. No Swagger UI: botão **Authorize** → cole o token.

São públicos apenas: `/api/auth/**`, `/api/public/**` (acompanhamento do cliente), `/health` e a documentação.

## 9. Instruções para execução dos testes
```bash
# só com a biblioteca padrão + dependências de runtime (sem instalar nada extra):
python -m unittest discover -s tests -t .

# com pytest e cobertura (recomendado) — requisito: >= 80% nos domínios críticos
pip install -r requirements-dev.txt
pytest --cov=app/domain --cov=app/application --cov-report=term-missing --cov-fail-under=80
```
- **Unitários** (`tests/domain`): objetos de valor, regras de estoque, orçamento e transições de status.
- **Integração** (`tests/api`): API REST + casos de uso + persistência + JWT — fluxo completo da OS, rollback por estoque insuficiente, rejeição de orçamento, CRUDs, validações e segurança. A mesma suíte roda com a persistência em memória e com SQLAlchemy/SQLite (esta é pulada automaticamente se o SQLAlchemy não estiver instalado).
- `tests/infrastructure`: JWT e Unit of Work.

## 10. Acesso ao Swagger / documentação da API
- Swagger UI: `http://localhost:8080/swagger-ui` (carrega os assets via CDN)
- OpenAPI (JSON): `http://localhost:8080/openapi.json` (gerado a partir das rotas registradas)

## 11. Exemplo rápido do fluxo (curl)
```bash
TOKEN=$(curl -s -X POST localhost:8080/api/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | sed 's/.*"token": *"\([^"]*\)".*/\1/')
H="Authorization: Bearer $TOKEN"; J='Content-Type: application/json'

curl -X POST localhost:8080/api/admin/clientes  -H "$H" -H "$J" -d '{"nome":"João","documento":"529.982.247-25","email":"joao@email.com"}'
curl -X POST localhost:8080/api/admin/servicos  -H "$H" -H "$J" -d '{"nome":"Troca de óleo","preco":80.00}'
curl -X POST localhost:8080/api/admin/pecas     -H "$H" -H "$J" -d '{"codigo":"FO-1","nome":"Filtro de óleo","preco":25.50,"quantidadeEstoque":10,"estoqueMinimo":2}'

curl -X POST localhost:8080/api/admin/ordens-servico -H "$H" -H "$J" -d '{
  "documentoCliente":"529.982.247-25",
  "veiculo":{"placa":"ABC1D23","marca":"Fiat","modelo":"Uno","ano":2018},
  "servicosIds":[1], "pecas":[{"pecaId":1,"quantidade":2}]}'

curl -X POST localhost:8080/api/admin/ordens-servico/1/diagnostico      -H "$H"
curl -X POST localhost:8080/api/admin/ordens-servico/1/orcamento/enviar -H "$H"
# cliente (sem JWT), usando o codigoAcompanhamento retornado na abertura da OS:
curl localhost:8080/api/public/acompanhamento/<codigo>
curl -X POST localhost:8080/api/public/acompanhamento/<codigo>/orcamento/aprovar
curl -X POST localhost:8080/api/admin/ordens-servico/1/finalizar -H "$H"
curl -X POST localhost:8080/api/admin/ordens-servico/1/entregar  -H "$H"
curl localhost:8080/api/admin/metricas/tempo-medio-execucao -H "$H"
```

## 12. Principais endpoints
| Área | Rotas |
|---|---|
| Auth | `POST /api/auth/login` |
| CRUD | `/api/admin/clientes`, `/veiculos`, `/servicos`, `/pecas` (+ `/pecas/{id}/estoque/entrada\|saida`, `/pecas/estoque-baixo`) |
| OS (admin) | `POST/GET /api/admin/ordens-servico`, `GET /{id}`, `POST /{id}/itens\|diagnostico\|orcamento/enviar\|orcamento/aprovar\|orcamento/rejeitar\|finalizar\|entregar` |
| Cliente (público) | `GET /api/public/acompanhamento/{codigo}`, `POST .../orcamento/aprovar\|rejeitar` |
| Métricas | `GET /api/admin/metricas/tempo-medio-execucao` |

Códigos de erro: `400` dados inválidos · `401` não autenticado · `404` não encontrado · `409` conflito (duplicidade/registro em uso) · `422` regra de negócio violada.

## 13. Estrutura dos principais diretórios
```
├── Dockerfile / docker-compose.yml / requirements*.txt / wsgi.py
├── app/
│   ├── factory.py, config.py, container.py   # composição da aplicação
│   ├── domain/                               # Python puro: agregados, VOs, regras
│   ├── application/                          # casos de uso, portas, comandos
│   ├── infrastructure/
│   │   ├── persistence/                      # sqlalchemy_* (PostgreSQL) e memory
│   │   └── security/                         # JWT
│   └── interfaces/                           # blueprints Flask, validação, OpenAPI, erros
├── tests/                                    # domain, api, infrastructure
└── docs/
    ├── ddd/                                  # Event Storming, linguagem ubíqua, diagramas, mapeamento
    ├── seguranca/                            # análise de vulnerabilidades
    └── ENTREGA.md                            # checklist do PDF de entrega
```

## 14. Links da entrega
- Documentação DDD (Miro): **<PREENCHER: link público do Miro>** — export em `docs/ddd/` (veja `docs/ddd/README.md`)
- Vídeo (YouTube, público, ≤ 15 min): **<PREENCHER>**
- Branch e hash do commit da entrega: **<PREENCHER>**
- Relatório de vulnerabilidades: [`docs/seguranca/`](docs/seguranca/)

## 15. Limitações conhecidas do MVP
- Schema criado por `Base.metadata.create_all` na subida (próxima fase: migrações com Alembic).
- Um único usuário administrador, definido por variáveis de ambiente.
- "Envio" do orçamento = disponibilização via API (sem e-mail/SMS/push).
- Swagger UI depende de CDN para os assets (o `/openapi.json` funciona offline).
#   o f i c i n a - p y  
 