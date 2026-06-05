## Avaliação do Exercício 1.2

### Resumo
O entregável é forte, completo e bem alinhado ao objetivo do exercício: projetar um system prompt auditável para um cenário RAG, testá-lo com chunks limitados e iterar com base em falhas reais. O participante demonstrou boa disciplina de contexto, análise crítica sobre os desvios do modelo e uma iteração v1 → v2 concreta. O principal ponto pendente é que a versão final ainda mantém uma regressão importante no caso de carga perigosa, o que impede nota máxima em qualidade do entregável.

### Scores por Dimensão

| Dimensão | Score | Justificativa |
|----------|-------|---------------|
| D1 — Domínio Conceitual | 3 | O participante demonstra compreensão real de engenharia de prompt e engenharia de contexto: separa contexto estático e dinâmico, estima tokens, define guardrails, trata exceção versus regra geral e reconhece o problema de extrapolação fora dos chunks. A análise não fica genérica; ela é aplicada ao comportamento esperado do RAG no cenário NovaTech. |
| D2 — Uso de Ferramentas | 3 | Há evidência de uso efetivo do Claude por meio de testes com 3 perguntas e registro dos resultados reais. O ciclo gerar → avaliar → iterar está visível, e a passagem de v1 para v2 não é cosmética: o participante endurece regras de escopo, restringe corpus ampliado e proíbe completar parâmetros ausentes. |
| D3 — Qualidade do Entregável | 2 | O artefato é completo, bem estruturado e utilizável, com prompt v1, prompt v2, mapeamento de contexto, testes e reflexão final. A nota não é 3 porque o resultado final ainda não fecha o comportamento desejado: o v2 melhora em 2 dos 3 testes, mas regrede justamente em uma pergunta crítica do exercício, então o prompt final ainda não está plenamente correto para uso sem ajuste adicional. |
| D4 — Pensamento Crítico | 3 | O participante não aceita os outputs do modelo de forma acrítica. Ele identifica desvios sutis, como contaminação pelo corpus ampliado, citação de seções fora do chunk e completude indevida de fórmula, além de perceber a regressão introduzida pelo v2 no caso de carga perigosa. Também reconhece explicitamente que será necessário um v3. |
| D5 — Aplicabilidade ao Projeto | 3 | O entregável está fortemente conectado ao contexto NovaTech: usa os documentos e casos do domínio, trabalha com política de devolução, tabela de SLA e procedimento de frete especial, e discute o comportamento esperado exatamente nas consultas operacionais do cenário. |

**Score do exercício: 2.8**

### Verificação de Armadilhas
- Armadilha obrigatória: “prazo de devolução para carga perigosa” não deve virar “7 dias úteis”; a resposta correta é que a exceção impede o processo padrão ou que a carga não é elegível no fluxo padrão. Identificada: sim. O participante reconheceu que o caso exige priorizar a exceção e apontou a regressão do v2 por não usar o chunk correto.
- Armadilha: confundir SLA de resolução com SLA de primeira resposta. Identificada: sim. O participante testou explicitamente esse risco e validou que a resposta correta era “até 24h”.
- Armadilha: inventar valor final do frete quando só há fórmula parcial. Identificada: sim. O participante apontou corretamente que o modelo não poderia completar a fórmula com parâmetro ausente e criticou o uso indevido do fator de peso.
- Armadilha: iteração cosmética entre v1 e v2. Identificada e evitada: sim. As mudanças foram funcionais e motivadas pelos erros observados, não apenas de redação.
- Regra “humano primeiro, IA depois”: não se aplica a este exercício nos termos da skill fornecida.

### Pontos Fortes
- System prompt específico, com identidade, guardrails, prioridade de decisão, regras de escopo e formato de resposta.
- Mapeamento de contexto estático e dinâmico bem documentado, com estimativas de tokens e interpretação correta do objetivo do exercício.
- Análise crítica forte dos testes, especialmente ao separar erro factual de erro de governança de contexto.

### Pontos de Melhoria
- Fechar a iteração com uma v3 mínima e validada, porque o v2 ainda falha em um caso central do exercício.
- Tornar o critério de uso afirmativo do chunk mais explícito, para evitar recusa indevida quando a evidência suficiente está presente.
- Refinar o formato de resposta para exigir citação mais precisa da fonte quando a seção estiver disponível no próprio chunk, reduzindo respostas genéricas.

### Classificação
Aprovado com distinção

### Tópicos da Trilha para Reforço
- Balanceamento entre guardrails de escopo e uso afirmativo do contexto recuperado.
- Engenharia de contexto em cenários RAG com foco em responder parcialmente quando há evidência suficiente, sem cair em recusa excessiva.
- Estratégias de iteração de prompt orientadas por regressão, para evitar corrigir extrapolação introduzindo under-answering.