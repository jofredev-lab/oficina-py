# Mapeamento: documentação DDD → código

| Conceito DDD | Elemento | Módulo / classe |
|---|---|---|
| Agregado (raiz) | Ordem de Serviço | `app/domain/ordem_servico.py` → `OrdemServico` |
| Agregado (raiz) | Cliente · Veículo · Serviço · Peça | `domain/cliente.py` · `domain/veiculo.py` · `domain/servico.py` · `domain/peca.py` |
| Entidade interna | Itens da OS | `ItemServico`, `ItemPeca` (imutáveis, preço congelado) |
| Objeto de valor | CPF/CNPJ · Placa | `Documento` · `Placa` (`@dataclass(frozen=True)`, validação na criação) |
| Enum de domínio | Status da OS · Status do orçamento | `StatusOS` (tabela de transições) · `OrcamentoStatus` |
| Comandos | Abrir OS, enviar orçamento, aprovar, finalizar, entregar… | métodos de `application/ordens.py::OrdemServicoService` e rotas em `interfaces/api/ordens.py` / `acompanhamento.py` |
| Eventos de domínio | OS aberta, orçamento enviado/aprovado/rejeitado, execução finalizada, veículo entregue | transições de estado em `OrdemServico` (persistidas em `status`, `orcamento_status` e datas). *No MVP os eventos são implícitos — não há barramento de eventos.* |
| Políticas / regras | Transições, itens bloqueados, estoque suficiente, orçamento sem itens | `StatusOS`, `OrdemServico`, `Peca` |
| Serviço de aplicação | Casos de uso | `app/application/cadastros.py`, `app/application/ordens.py` |
| Portas (repositórios e Unit of Work) | Contratos de persistência | `app/application/ports.py` |
| Adaptadores de persistência | PostgreSQL (SQLAlchemy) e memória | `infrastructure/persistence/sqlalchemy_repositories.py` · `memory.py` |
| Transação | Unit of Work (commit/rollback) | `SqlAlchemyUnitOfWork`, `InMemoryUnitOfWork` |
| Exceções de domínio | Regra violada · não encontrado · conflito | `RegraNegocioError` (422) · `RecursoNaoEncontradoError` (404) · `ConflitoError` (409) |
| Linguagem ubíqua | Nomes em português do domínio | classes, métodos, status e rotas |

> O domínio **não importa** Flask nem SQLAlchemy: ele só conhece Python puro. A persistência é injetada por meio das portas.
