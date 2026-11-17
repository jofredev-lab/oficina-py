# Análise de vulnerabilidades

> **Preencher com o resultado real** antes da entrega (rode os comandos abaixo e anexe/cole o resultado).

## Dependências (pip-audit)
```bash
pip install pip-audit
pip-audit -r requirements.txt | tee docs/seguranca/pip-audit.txt
```

## Código-fonte (Bandit — análise estática)
```bash
pip install bandit
bandit -r app -f txt -o docs/seguranca/bandit.txt
```

## Dependências, configuração e imagem Docker (Trivy)
```bash
trivy fs --severity HIGH,CRITICAL . > docs/seguranca/trivy-fs.txt
trivy image oficina-flask:latest > docs/seguranca/trivy-image.txt   # após docker build -t oficina-flask .
```
O workflow `.github/workflows/ci.yml` também executa pip-audit, Bandit e Trivy e publica os relatórios como artefatos.

## Controles de segurança implementados
| Controle | Implementação |
|---|---|
| Autenticação JWT (HS256) nas APIs administrativas (`/api/admin/**`) | `infrastructure/security/jwt_service.py`, `interfaces/api/support.py::exigir_admin` |
| Segredo JWT com mínimo de 32 caracteres (a aplicação não sobe com segredo curto); tokens com `exp` obrigatório | `JwtService` |
| Senha do admin guardada como hash (scrypt/Werkzeug); comparação em tempo constante do usuário | `AuthService` |
| Credenciais e segredos via variáveis de ambiente (nenhum segredo real no repositório) | `app/config.py`, `docker-compose.yml` |
| Validação de entrada (tipos, obrigatoriedade, limites) e de dados sensíveis (CPF/CNPJ, placa) | `interfaces/validation.py`, `Documento`, `Placa` |
| SQL parametrizado via SQLAlchemy ORM, sem concatenação de SQL | `sqlalchemy_repositories.py` |
| Acompanhamento público por UUID aleatório; resposta sem dados pessoais | `acompanhamento_json` |
| Erros padronizados (RFC 7807) sem vazar stack trace | `interfaces/errors.py` |
| Container executa com usuário não-root | `Dockerfile` |

## Resultado da análise
| Ferramenta | Data | Resultado | Ação |
|---|---|---|---|
| pip-audit | __ | __ | __ |
| Bandit | __ | __ | __ |
| Trivy | __ | __ | __ |
