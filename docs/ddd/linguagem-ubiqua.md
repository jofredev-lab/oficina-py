# Linguagem Ubíqua e Glossário

Os termos abaixo são usados de forma idêntica na conversa com o negócio, na documentação e no código (nomes de classes, métodos, status e rotas).

| Termo | Definição | No código |
|---|---|---|
| **Cliente** | Pessoa física ou jurídica dona do veículo, identificada por CPF/CNPJ. | `app/domain/cliente.py` → `Cliente`, `Documento` |
| **Documento** | CPF (11 dígitos) ou CNPJ (14 dígitos) válido, guardado só com dígitos. | `Documento`, `TipoDocumento` |
| **Veículo** | Carro atendido pela oficina, identificado pela placa e vinculado a um cliente. | `app/domain/veiculo.py` → `Veiculo`, `Placa` |
| **Placa** | Identificação do veículo (padrão antigo `ABC1234` ou Mercosul `ABC1D23`). | `Placa` |
| **Serviço** | Mão de obra do catálogo da oficina (ex.: troca de óleo, alinhamento), com preço. | `app/domain/servico.py` → `Servico` |
| **Peça / Insumo** | Item de estoque usado no reparo (ex.: filtro, óleo), com preço, saldo e estoque mínimo. | `app/domain/peca.py` → `Peca` |
| **Ordem de Serviço (OS)** | Registro de todo o atendimento de um veículo: itens, orçamento, status e datas. | `app/domain/ordem_servico.py` → `OrdemServico` |
| **Item de serviço / Item de peça** | Serviço ou peça incluída na OS; guarda o preço do momento da inclusão. | `ItemServico`, `ItemPeca` |
| **Diagnóstico** | Avaliação do veículo pela oficina para definir o que será feito. | `StatusOS.EM_DIAGNOSTICO` |
| **Orçamento** | Valor total da OS (serviços + peças × quantidade), gerado automaticamente e enviado ao cliente. | `OrdemServico.valor_total`, `OrcamentoStatus` |
| **Aprovação / Rejeição** | Decisão do cliente sobre o orçamento. Aprovar inicia a execução; rejeitar encerra a OS sem execução. | `aprovar_orcamento()`, `rejeitar_orcamento()` |
| **Execução** | Período em que a oficina realiza os serviços (da aprovação à finalização). | `StatusOS.EM_EXECUCAO`, `duracao_execucao()` |
| **Finalizada** | Serviço concluído (ou OS encerrada por rejeição), veículo pronto para retirada. | `StatusOS.FINALIZADA` |
| **Entregue** | Veículo devolvido ao cliente. Estado final. | `StatusOS.ENTREGUE` |
| **Código de acompanhamento** | Código aleatório (UUID) que o cliente usa para consultar a OS e aprovar o orçamento. | `codigo_acompanhamento` |
| **Baixa de estoque** | Redução do saldo das peças da OS no momento da aprovação. | `Peca.baixar_estoque()` |
| **Estoque baixo** | Saldo menor ou igual ao estoque mínimo. | `Peca.estoque_baixo` |
| **Tempo médio de execução** | Média das durações de execução das OS que foram executadas. | `OrdemServicoService.tempo_medio_execucao()` |

## Status da OS (valores exatos)
`RECEBIDA` (Recebida) · `EM_DIAGNOSTICO` (Em diagnóstico) · `AGUARDANDO_APROVACAO` (Aguardando aprovação) · `EM_EXECUCAO` (Em execução) · `FINALIZADA` (Finalizada) · `ENTREGUE` (Entregue)

## Status do orçamento
`NAO_GERADO` → `PENDENTE` → `APROVADO` ou `REJEITADO`
