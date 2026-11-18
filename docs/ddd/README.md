# Documentação DDD

Esta pasta contém a documentação textual (Markdown + Mermaid) que **corresponde ao código entregue**.

| Arquivo | Conteúdo |
|---|---|
| [`event-storming.md`](event-storming.md) | Event Storming dos 3 fluxos: criação da OS, acompanhamento da OS e gestão de peças/insumos (eventos, comandos, políticas, atores, agregados) |
| [`event-storming-miro.md`](event-storming-miro.md) | Modelo completo de board Miro: autenticação, cadastros, estoque, ciclo da OS, consultas, desvios e pontos de atenção |
| [`diagramas.md`](diagramas.md) | Mapa de contextos, modelo de domínio (agregados/entidades/VOs), máquina de estados da OS e sequência da aprovação |
| [`linguagem-ubiqua.md`](linguagem-ubiqua.md) | Linguagem ubíqua e glossário |
| [`mapeamento-codigo.md`](mapeamento-codigo.md) | Relação entre cada conceito DDD e o módulo/classe Python que o implementa |

## O que falta fazer (manual)
1. Reproduzir o board no **Miro** (ou ferramenta equivalente) usando `event-storming-miro.md` como modelo — cores clássicas: laranja = evento, azul = comando, amarelo = ator, rosa/lilás = política, amarelo-claro = agregado.
2. Deixar o board com acesso público para visualização (sem pedir permissão) e colocar o link no `README.md` raiz e no PDF.
3. Exportar o board para `docs/ddd/event-storming.pdf` e os diagramas para `docs/ddd/diagramas.pdf` (ou imagens), mantendo no repositório.
