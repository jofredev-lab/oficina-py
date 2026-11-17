# Diagramas

## 1. Mapa de contextos
```mermaid
flowchart LR
  subgraph Core[Atendimento e Execução - core]
    OS[OrdemServico]
  end
  subgraph Cad[Cadastros]
    CL[Cliente]
    VE[Veiculo]
  end
  subgraph Est[Catálogo e Estoque]
    SV[Servico]
    PC[Peca]
  end
  OS -- referencia --> CL
  OS -- referencia --> VE
  OS -- referencia + snapshot de preço --> SV
  OS -- referencia + snapshot de preço; baixa de estoque --> PC
  VE -- pertence a --> CL
```

## 2. Modelo de domínio (agregados, entidades e objetos de valor)
```mermaid
classDiagram
  class OrdemServico {
    <<Aggregate Root>>
    +Long id
    +String codigo_acompanhamento
    +StatusOS status
    +OrcamentoStatus orcamentoStatus
    +abrir(cliente, veiculo)
    +adicionar_servico(servico)
    +adicionar_peca(peca, qtd)
    +iniciar_diagnostico()
    +enviar_orcamento()
    +aprovar_orcamento()
    +rejeitar_orcamento()
    +finalizar()
    +entregar()
    +valor_total()
    +duracao_execucao()
  }
  class ItemServico {
    <<Entity>>
    nome_servico
    preco
  }
  class ItemPeca {
    <<Entity>>
    nome_peca
    preco_unitario
    quantidade
    subtotal()
  }
  class Cliente {
    <<Aggregate Root>>
    nome
    email
    telefone
  }
  class Documento {
    <<Value Object>>
    numero
    tipo
  }
  class Veiculo {
    <<Aggregate Root>>
    marca
    modelo
    ano
  }
  class Placa {
    <<Value Object>>
    numero
  }
  class Servico {
    <<Aggregate Root>>
    nome
    descricao
    preco
  }
  class Peca {
    <<Aggregate Root>>
    codigo
    nome
    preco
    quantidade_estoque
    estoque_minimo
    baixar_estoque()
    repor_estoque()
  }
  OrdemServico "1" *-- "0..*" ItemServico
  OrdemServico "1" *-- "0..*" ItemPeca
  OrdemServico --> Cliente
  OrdemServico --> Veiculo
  ItemServico --> Servico
  ItemPeca --> Peca
  Cliente *-- Documento
  Veiculo *-- Placa
  Veiculo --> Cliente
```

## 3. Ciclo de vida da Ordem de Serviço
```mermaid
stateDiagram-v2
  [*] --> RECEBIDA: abrir OS
  RECEBIDA --> EM_DIAGNOSTICO: iniciar_diagnostico
  EM_DIAGNOSTICO --> AGUARDANDO_APROVACAO: enviar_orcamento
  AGUARDANDO_APROVACAO --> EM_EXECUCAO: aprovar_orcamento (baixa estoque)
  AGUARDANDO_APROVACAO --> FINALIZADA: rejeitar_orcamento
  EM_EXECUCAO --> FINALIZADA: finalizar
  FINALIZADA --> ENTREGUE: entregar
  ENTREGUE --> [*]
```

## 4. Sequência: aprovação do orçamento pelo cliente
```mermaid
sequenceDiagram
  actor C as Cliente
  participant API as Blueprint acompanhamento
  participant S as OrdemServicoService (Unit of Work)
  participant OS as OrdemServico
  participant P as Peca
  C->>API: POST /api/public/acompanhamento/{codigo}/orcamento/aprovar
  API->>S: aprovarPorCodigo(codigo)
  S->>OS: aprovar_orcamento()
  OS-->>S: status = EM_EXECUCAO
  loop cada item de peça
    S->>P: baixar_estoque(qtd)
    P-->>S: ok / RegraNegocioError
  end
  S-->>API: commit (ou rollback se faltar estoque)
  API-->>C: 200 (ou 422)
```
