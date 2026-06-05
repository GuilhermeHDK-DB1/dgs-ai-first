## Avaliação do Exercício 1.1

### Resumo
O entregável demonstra boa compreensão técnica de RAG e engenharia de contexto, com análise específica para tipos de fonte, riscos de conflito entre versões e implicações de orçamento de contexto. O ponto mais forte é o raciocínio crítico sobre qualidade de recuperação e governança documental; o principal gap é a ausência de evidência da iteração com o Claude, que era parte obrigatória do exercício. A estimativa de volume também ficou um pouco otimista para o cenário descrito, o que reduz a robustez prática da análise.

### Scores por Dimensão

| Dimensão | Score | Justificativa |
|----------|-------|---------------|
| D1 — Domínio Conceitual | 3 | O participante demonstra domínio real dos conceitos centrais: trata RAG como problema de engenharia de dados e contexto, explica bem `lost in the middle`, diferencia precisão de cobertura, propõe chunking semântico e reconhece riscos como OCR ruim, tabelas mal extraídas e conflito entre versões de procedimentos. |
| D2 — Uso de Ferramentas | 1 | O exercício exigia uso do Claude com revisão crítica e incorporação do feedback, além do histórico de iteração. No material entregue, não há evidência do ciclo gerar → revisar → iterar, nem comparação entre versão inicial e versão revisada. Isso impede validar uso efetivo da ferramenta e aciona o red flag de “sem iteração”. |
| D3 — Qualidade do Entregável | 2 | A análise final é útil, organizada e tecnicamente consistente, mas o entregável está incompleto frente ao enunciado porque não traz o histórico de iteração com o Claude. Além disso, a estimativa total de ~5,2M tokens mostra cálculo e premissas explícitas, mas ficou abaixo da faixa mais plausível esperada pela rubrica para score máximo, sugerindo premissas otimistas. |
| D4 — Pensamento Crítico | 3 | Há julgamento próprio e não apenas repetição genérica de discurso sobre IA. O participante identifica riscos sutis e concretos, como mistura entre `PROC-042` e `PROC-042-v2`, uso indevido de FAQ como fonte primária, necessidade de peso menor para OCR de baixa confiança e limitação de usar RAG puro para planilhas com lógica de cálculo. |
| D5 — Aplicabilidade ao Projeto | 2 | O texto está bem conectado ao domínio NovaTech, citando documentos, versões, tipos de conteúdo e perguntas reais de atendimento. Ainda assim, poderia integrar mais explicitamente restrições do projeto e do cenário operacional, como atualização mensal por áreas distintas, ambiente Microsoft/Azure já disponível, volume de chamados e metas de tempo de atendimento. |

**Score do exercício: 2.2**

### Verificação de Armadilhas
Nenhuma armadilha intencional explícita foi definida para este exercício na skill de avaliação.  
O ponto de verificação obrigatório aqui era a iteração com o Claude, e ela não foi evidenciada no entregável.

### Pontos Fortes
- A análise por tipo de fonte é específica e útil: não cai em simplificações como “converter tudo para texto”.
- A seção de orçamento de contexto mostra entendimento correto de que janela grande não elimina a necessidade de retrieval seletivo.
- A estratégia de chunking está bem justificada pelo tipo de pergunta e pelo risco de perda de atenção em contextos longos.

### Pontos de Melhoria
- Incluir o histórico real de iteração com o Claude: prompt usado, crítica recebida, versão anterior e mudanças incorporadas.
- Recalibrar a estimativa de tokens com cenários mais conservadores, especialmente para PDFs extensos, tabelas densas e planilhas com extração expandida.
- Conectar a análise técnica com mais restrições do projeto NovaTech, como cadência de atualização documental, ambiente Microsoft/Azure e meta operacional de redução do tempo de busca.

### Classificação
Aprovado

### Tópicos da Trilha para Reforço
- Uso de ferramentas com evidência e iteração verificável.
- Estimativas práticas de volume e capacidade em RAG.
- Tradução de análise técnica para entregável completo aderente ao enunciado.
