# Exercício 1.2 — Entendimento

## 1. O que o exercício está pedindo de fato

O Exercício 1.2 não pede apenas a escrita de um system prompt. Ele avalia se o participante consegue desenhar o contexto de uma aplicação RAG de forma consciente, testá-lo em um modelo real e iterar com base em falhas observadas.

Na prática, o exercício mede quatro capacidades ao mesmo tempo:

1. Escrever um `system prompt` específico, com regras claras e prioridades explícitas entre fontes.
2. Separar corretamente o que é contexto estático e o que é contexto dinâmico.
3. Testar o comportamento real do modelo com chunks limitados e potencialmente incompletos.
4. Diagnosticar erros de resposta e ajustar o prompt de forma verificável entre uma v1 e uma v2.

O ponto central é este: o participante não deve provar apenas que sabe orientar o modelo; ele deve provar que sabe fazê-lo falhar corretamente quando faltar informação.

## 2. Insumos obrigatórios do exercício

### 2.1 Cenário base

O cenário continua sendo o da NovaTech: assistente para atendimento interno, integrado ao ambiente Microsoft, com foco em responder dúvidas sobre devolução, SLA, frete e procedimentos com base documental.

### 2.2 Guardrails obrigatórios

O prompt precisa incorporar explicitamente estes quatro guardrails:

1. Sempre citar a fonte do documento.
2. Nunca inventar prazos ou valores que não estejam na documentação.
3. Quando não encontrar resposta suficiente, dizer isso explicitamente e sugerir escalar para o supervisor.
4. Responder em português formal, mas acessível.

### 2.3 Chunks simulados a usar

O exercício fornece exatamente três chunks para o teste inicial.

**Chunk A**

> "Política de Devolução POL-001, seção 3.2: Mercadorias podem ser devolvidas em até 7 dias úteis após o recebimento, exceto cargas classificadas como perigosas (classes 1 a 6 da ANTT). O cliente deve abrir chamado no portal e anexar fotos da mercadoria."

**Chunk B**

> "Tabela SLA-2024: Cliente Gold — resposta em até 2h, resolução em até 24h. Cliente Silver — resposta em até 4h, resolução em até 48h. Cliente Standard — resposta em até 8h, resolução em até 72h."

**Chunk C**

> "PROC-042-v2, seção 2: Frete especial para cargas acima de 500kg: valor base × multiplicador regional. Região Sul: 1.3. Região Sudeste: 1.1. Região Norte: 1.8. Região Nordeste: 1.5. Região Centro-Oeste: 1.4."

### 2.4 Restrição crítica

O assistente só deveria usar a informação presente nesses chunks durante os testes do exercício. Isso é importante porque uma boa parte da avaliação está em saber recusar ou responder parcialmente quando o contexto recuperado é insuficiente.

## 3. O que precisa existir no system prompt

O prompt v1 deve ser completo e organizado. A estrutura mais segura é esta:

1. Identidade do assistente.
2. Objetivo do assistente no contexto NovaTech.
3. Regras invioláveis.
4. Ordem de prioridade entre fontes e evidências.
5. Formato de resposta.
6. Instruções de como usar os chunks.
7. Regra explícita para dado ausente ou insuficiente.

O enunciado pede especificamente que o prompt defina a ordem de prioridade quando houver conflito entre fontes. Mesmo que os três chunks de teste não tragam um conflito forte entre si, o entregável precisa demonstrar que o autor pensou nesse caso.

## 4. Engenharia de contexto que precisa ser documentada

O exercício não quer só o texto do prompt. Ele quer que o participante documente a anatomia do contexto.

### 4.1 Contexto estático

São os elementos que entram em toda consulta:

1. Identidade do assistente.
2. Guardrails.
3. Regras de prioridade entre fontes.
4. Formato de resposta.
5. Instruções sobre o que fazer quando faltarem dados.

### 4.2 Contexto dinâmico

São os elementos que mudam a cada pergunta:

1. Chunks recuperados pelo RAG.
2. Pergunta do atendente.
3. Dados adicionais do cliente, se houver.
4. Histórico da conversa, se houver.

### 4.3 O que precisa ser mostrado

O entregável deve identificar quais partes são estáticas e quais são dinâmicas, e estimar o tamanho aproximado em tokens de cada uma. O objetivo não é precisão absoluta; é demonstrar que o participante entende composição e orçamento de contexto.

## 5. Respostas esperadas para as 3 perguntas de teste

### 5.1 Pergunta 1

**Pergunta:** "Qual o prazo de devolução para carga perigosa?"

**Resposta esperada:**

O assistente deve responder que cargas perigosas não se enquadram no processo padrão de devolução descrito no chunk, porque há uma exceção explícita para cargas classificadas como perigosas. A resposta correta não é "7 dias úteis". Ela deve priorizar a exceção, citar a `POL-001, seção 3.2` e evitar inventar procedimento adicional que não esteja presente no chunk.

### 5.2 Pergunta 2

**Pergunta:** "Meu cliente é Gold, qual o SLA de resolução?"

**Resposta esperada:**

O assistente deve responder `até 24h` e citar a `SLA-2024`. O erro clássico aqui é confundir SLA de resolução com SLA de primeira resposta, que no mesmo chunk é `2h`.

### 5.3 Pergunta 3

**Pergunta:** "Quanto custa o frete para 600kg para Manaus?"

**Resposta esperada:**

O assistente não deve inventar um valor final. O chunk informa a fórmula e o multiplicador da região Norte, mas não informa o valor base. Portanto, a resposta correta é parcial: deve dizer que não é possível calcular o valor exato com a documentação disponível, citar a `PROC-042-v2`, informar que Manaus está na região Norte e que o multiplicador regional é `1.8`, e sugerir escalonamento ou consulta adicional para obter o valor base.

## 6. Principais armadilhas do exercício

### 6.1 Ignorar exceção e responder a regra geral

A principal armadilha explícita é a pergunta sobre carga perigosa. Se o participante ou o prompt tratar a resposta como `7 dias úteis`, falhou em interpretar a exceção do próprio chunk.

### 6.2 Inventar valor quando há só fórmula parcial

Na pergunta sobre frete para 600kg em Manaus, o sistema pode ser tentado a preencher a lacuna do valor base. Isso é falha direta contra os guardrails.

### 6.3 Confundir citação com precisão

Citar uma fonte não basta. O modelo pode citar `POL-001` e ainda responder errado. O participante precisa avaliar a correção factual da resposta, não apenas a presença de uma referência.

### 6.4 Fazer iteração cosmética

O exercício pede v1 e v2. Se a mudança for apenas de redação, sem correção concreta de comportamento, a iteração não demonstra aprendizado real.

### 6.5 Tratar o exercício como caso fechado e fácil

Mesmo com apenas três chunks, o bom entregável deve reconhecer que esse cenário é simplificado. Em produção, retrieval imperfeito, conflitos de versão e competição entre chunks tornam o problema mais difícil.

## 7. O que tende a pesar mais na avaliação

O avaliador tende a procurar estes sinais:

1. O prompt é específico ou genérico?
2. O mapeamento estático/dinâmico foi realmente feito?
3. As respostas de teste são reais e documentadas?
4. O participante identificou corretamente a falha sobre carga perigosa?
5. A v2 corrige algo concreto da v1?
6. O participante reconhece os limites do prompt quando o contexto recuperado é insuficiente?

## 8. Estrutura recomendada de entregável

Uma estrutura forte para o Exercício 1.2 é esta:

1. `System Prompt v1`.
2. `Mapeamento de contexto estático e dinâmico`, com estimativa de tokens.
3. `Teste v1`, contendo as 3 perguntas, as respostas reais do Claude e a análise crítica de cada uma.
4. `System Prompt v2`, com destaque para as mudanças.
5. `Teste v2`, repetindo as 3 perguntas e mostrando a melhoria.
6. `Reflexão final`, explicando o que melhorou, o que ainda é frágil e o que dependeria do retrieval em produção.

## 9. Síntese prática

O Exercício 1.2 testa se o participante entende que prompt engineering, em contexto de RAG, não é só redação. É desenho de comportamento sob restrições. A melhor resposta não é a mais confiante; é a mais disciplinada em relação ao contexto disponível.

Se o entregável mostrar um prompt auditável, testes reais, diagnóstico honesto das falhas e uma iteração que melhora o comportamento do modelo, ele atende o espírito e a forma do exercício.