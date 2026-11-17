# Checklist do PDF de entrega (Fase 1)

**Primeira página do PDF** (preencher):
- Curso: SOAT — Software Architecture · Fase: 1 · Grupo: __
- Integrantes (nome completo, RM, username no Discord): __
- Linguagem e tecnologias: Python 3.12, Flask 3, SQLAlchemy 2, PostgreSQL, JWT (PyJWT), Swagger/OpenAPI, Docker, unittest/pytest + coverage

**Links clicáveis a incluir**
- [ ] Repositório GitHub público (+ branch e hash do commit final)
- [ ] Vídeo no YouTube (público, ≤ 15 min)
- [ ] Documentação DDD no Miro (acessível sem pedir permissão)

**Antes de entregar**
- [ ] `main` protegida; tudo entra via Pull Request
- [ ] `pytest --cov=app/domain --cov=app/application --cov-fail-under=80` passou — anexar print/relatório
- [ ] `docker compose up --build` sobe tudo do zero
- [ ] Export do Miro salvo em `docs/ddd/` (`event-storming.pdf`, `diagramas.pdf`)
- [ ] Relatório de vulnerabilidades salvo em `docs/seguranca/`
- [ ] Nenhuma credencial real no repositório

**Roteiro do vídeo (≤ 15 min)**: proposta · arquitetura e camadas · banco e justificativa · Event Storming · elementos de DDD · criar OS (serviços e peças) · orçamento e aprovação · mudanças de status · JWT · Swagger · testes e cobertura · análise de vulnerabilidades · integrantes.
