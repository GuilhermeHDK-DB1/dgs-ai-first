# Exercício 1.3 — Entendimento

## 1. O que o exercício está pedindo de fato

O Exercício 1.3 não pede apenas um protótipo qualquer de busca semântica. Ele pede uma prova de conceito funcional de RAG que permita avaliar, com stack open-source, se a NovaTech consegue recuperar contexto útil e montar respostas fundamentadas antes de investir em Azure.

Na prática, o exercício mede cinco capacidades ao mesmo tempo:

1. Ingerir documentos reais em formato utilizável por um pipeline.
2. Definir uma estratégia de chunking justificada pelo tipo de conteúdo.
3. Recuperar chunks relevantes com embeddings e vector store.
4. Montar um prompt que o LLM consiga usar sem inventar informação.
5. Avaliar criticamente os resultados com base em um gabarito explícito.

O ponto central é este: a entrega não deve provar apenas que o código roda. Ela deve provar que o participante entende RAG como sistema de engenharia de dados, retrieval e validação, e não como simples chamada de biblioteca.

## 2. Insumos obrigatórios do exercício

### 2.1 Input do pipeline: Anexo A

Os documentos a serem ingeridos estão na pasta [assets/anexos/anexo-a-documentos-individuais](d:/dgs-ai-first/assets/anexos/anexo-a-documentos-individuais). São estes 5 arquivos markdown:

1. [POL-001-politica-devolucao.md](d:/dgs-ai-first/assets/anexos/anexo-a-documentos-individuais/POL-001-politica-devolucao.md)
2. [PROC-042-frete-especial-v1.md](d:/dgs-ai-first/assets/anexos/anexo-a-documentos-individuais/PROC-042-frete-especial-v1.md)
3. [PROC-042-v2-frete-especial-revisado.md](d:/dgs-ai-first/assets/anexos/anexo-a-documentos-individuais/PROC-042-v2-frete-especial-revisado.md)
4. [SLA-2024-tabela-sla-clientes.md](d:/dgs-ai-first/assets/anexos/anexo-a-documentos-individuais/SLA-2024-tabela-sla-clientes.md)
5. [FAQ-atendimento.md](d:/dgs-ai-first/assets/anexos/anexo-a-documentos-individuais/FAQ-atendimento.md)

Esses arquivos são o input bruto do pipeline. Eles devem ser lidos, divididos em chunks, convertidos em embeddings e armazenados em um vector store.

### 2.2 Benchmark de validação: Anexo B

O gabarito de retrieval está em [anexo-b-chunks-referencia-rag.md](d:/dgs-ai-first/assets/anexos/anexo-b-chunks-referencia-rag.md).

Esse anexo deve ser usado para dois objetivos:

1. Validar se o pipeline recuperou os chunks esperados para cada pergunta.
2. Identificar armadilhas intencionais, como conflito entre versões e perguntas sem cobertura documental.

Em outras palavras:

1. O Anexo A alimenta o pipeline.
2. O Anexo B mede a qualidade do pipeline.

## 3. Componentes mínimos do pipeline

Para ser considerado funcional, o pipeline precisa ter pelo menos quatro blocos bem definidos.

### 3.1 Ingestão

Um script ou módulo precisa:

1. Ler os 5 arquivos markdown.
2. Dividir o conteúdo em chunks.
3. Gerar embeddings para cada chunk.
4. Persistir esses chunks em um vector store com metadados.

### 3.2 Busca

Uma função precisa:

1. Receber uma pergunta em linguagem natural.
2. Gerar o embedding da pergunta.
3. Consultar o vector store.
4. Retornar os `N` chunks mais similares com score de similaridade.

### 3.3 Montagem de prompt

Uma função precisa receber a pergunta e os chunks recuperados e montar um prompt completo para o LLM, normalmente composto por:

1. Um system prompt com guardrails.
2. O contexto recuperado.
3. A pergunta do usuário.

### 3.4 Geração e avaliação

O prompt montado precisa ser testado no Claude, conforme o enunciado. A avaliação da resposta deve verificar:

1. Se a resposta está correta.
2. Se cita fonte.
3. Se respeita guardrails.
4. Se deixa de responder quando não há informação suficiente.

Se algum desses blocos não existir, o pipeline fica incompleto para a rubrica.

## 4. O que a estratégia de chunking precisa demonstrar

O exercício explicitamente penaliza soluções do tipo “512 tokens fixos porque sim”. Portanto, a estratégia de chunking precisa ser justificada.

O melhor entendimento para este caso é:

1. Documentos normativos e procedimentais tendem a funcionar melhor com chunking por seção ou subseção.
2. Tabelas devem ser preservadas como unidade lógica sempre que possível.
3. Itens de FAQ devem ser chunkados por pergunta/resposta, e não como um bloco longo inteiro.
4. Versões diferentes do mesmo procedimento nunca devem ser misturadas no mesmo chunk.

O racional é simples: as perguntas do atendimento são pontuais e geralmente correspondem a uma seção específica, uma linha de tabela ou uma FAQ individual.

## 5. Perguntas de teste mais adequadas

O enunciado pede ao menos 5 perguntas do mapa de cobertura do Anexo B. O melhor conjunto para maximizar cobertura da rubrica é este:

### 5.1 Pergunta 1

**"Qual o prazo de devolução?"**

Serve como baseline. Verifica se o pipeline recupera chunks corretos de política sem complicações excessivas.

### 5.2 Pergunta 2

**"Posso devolver carga perigosa?"**

Testa a armadilha de negação explícita. O correto é recuperar `POL-001-B`, não apenas a regra geral de devolução.

### 5.3 Pergunta 3

**"Qual o SLA do cliente Gold?"**

Testa recuperação em outro domínio documental e em conteúdo tabelado.

### 5.4 Pergunta 4

**"Qual o SLA do cliente Platinum?"**

Testa alucinação. O pipeline ou o LLM não podem inventar um tier que não existe.

### 5.5 Pergunta 5

**"Frete para 600kg para Manaus?"**

Testa múltiplos chunks, fórmula, fator de peso, multiplicador regional e risco de conflito entre versões.

### 5.6 Sexta pergunta opcional, mas muito útil

**"Frete para 300kg para Salvador?"**

Essa pergunta é excelente para testar não-cobertura documental. Como o frete especial só cobre cargas acima de 500kg, o comportamento correto é não inventar resposta.

## 6. Armadilhas técnicas principais

### 6.1 Quebra de tabela no chunking

Se a tabela de multiplicadores ou SLAs for cortada no meio, o retrieval pode trazer respostas incompletas ou erradas.

### 6.2 Recuperação ruim de negação

Perguntas sobre elegibilidade podem recuperar chunks semanticamente próximos, mas ignorar a palavra `NÃO`, levando a inversão da regra.

### 6.3 Mistura entre PROC-042 v1 e v2

Esse é um dos riscos centrais do caso. Se o pipeline recuperar as duas versões ao mesmo tempo sem metadado de versão ou sem critério de priorização, o LLM pode misturar multiplicadores e fatores de peso.

### 6.4 Score alto não significa chunk correto

O participante não deve confiar apenas no score de similaridade. É preciso verificar se o chunk recuperado realmente responde à pergunta.

### 6.5 FAQ informal tratado como fonte forte

O FAQ é útil, mas é explicitamente informal. Se o pipeline ou o prompt o usarem como verdade normativa sem ressalva, a resposta perde confiabilidade.

## 7. Armadilhas de avaliação

Além das armadilhas técnicas, o exercício tem armadilhas de correção:

1. Apresentar apenas código sem evidência de que rodou.
2. Mostrar chunks recuperados sem comparar com o gabarito do Anexo B.
3. Dizer que a busca funcionou sem analisar a resposta final do LLM.
4. Inventar problemas em vez de relatar problemas efetivamente observados nos testes.
5. Tratar o pipeline como sucesso só porque “retornou algo”.

O avaliador tende a valorizar mais um pipeline simples que funciona e é analisado com honestidade do que uma solução sofisticada sem validação clara.

## 8. O que tende a pesar mais na rubrica

Os pontos que mais pesam para uma boa avaliação são estes:

1. O pipeline realmente roda de ponta a ponta.
2. O chunking foi justificado com base no tipo de documento.
3. Os testes usam perguntas reais do domínio e são comparados ao gabarito.
4. Pelo menos 2 problemas reais foram encontrados e explicados.
5. O participante demonstra que entendeu que RAG é um problema de retrieval e qualidade de contexto, não apenas de geração.

## 9. Estrutura recomendada de entregável

Uma estrutura forte para o Exercício 1.3 seria esta:

1. `README` com stack, objetivo, como rodar e visão geral do pipeline.
2. Código da ingestão.
3. Código da busca.
4. Código da montagem de prompt.
5. Resultados dos testes com tabela comparando pergunta, chunks retornados, score e chunks esperados.
6. Respostas do Claude para os prompts montados.
7. Análise crítica dos resultados.
8. Lista de problemas encontrados e propostas de correção.
9. Evidência de uso do Copilot e do Claude, porque o enunciado pede ambas as ferramentas.

## 10. Síntese prática

O Exercício 1.3 testa se o participante consegue construir um RAG mínimo viável e avaliá-lo como engenheiro, não como usuário impressionado com output de LLM. O comportamento esperado é pragmático: recuperar chunks corretos, medir erros com base no gabarito, reconhecer limitações do retrieval e propor melhorias concretas.

Se a entrega mostrar código funcional, testes bem escolhidos, comparação explícita com o Anexo B e problemas reais documentados com honestidade, ela atende o espírito e a forma do exercício.