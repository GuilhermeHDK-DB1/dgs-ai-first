# Exercício 1.1 — Análise de Viabilidade Técnica

## 1. Resumo executivo

É tecnicamente viável construir um assistente de IA para a NovaTech usando RAG, mas a qualidade da solução vai depender menos da janela de contexto do modelo e mais da qualidade da ingestão, da governança dos documentos e da disciplina na montagem do contexto. O principal risco não é falta de capacidade do LLM; é recuperar contexto incorreto, contraditório ou estruturalmente mal extraído.

Os documentos simulados já mostram três classes de problema que devem aparecer em produção: conflito entre versões do mesmo procedimento, fontes com pesos de confiabilidade diferentes e lacunas documentais. Portanto, a arquitetura precisa tratar RAG como um problema de engenharia de dados e de contexto, não apenas como busca vetorial acoplada a um modelo grande.

## 2. Viabilidade por tipo de fonte

### 2.1 PDFs com tabelas complexas

**Desafio para o pipeline de RAG**

PDFs com tabelas amplas tendem a perder estrutura quando extraídos como texto linear. Colunas podem ser embaralhadas, cabeçalhos podem se separar das linhas e tabelas extensas podem ser quebradas em trechos sem relação semântica clara.

**Impacto na qualidade das respostas**

Quando isso acontece, o embedding deixa de representar a regra de negócio real. O assistente pode recuperar um trecho com valores ou condições trocadas, ou combinar partes de linhas diferentes. Em perguntas de frete, SLA e políticas com exceções, esse erro gera resposta objetivamente incorreta com alta confiança.

**Estratégia de tratamento**

Usar extração estruturada antes do chunking, preservando a tabela como unidade lógica sempre que possível. Para tabelas grandes, quebrar por blocos semânticos de linhas, mantendo cabeçalhos repetidos em cada bloco. Armazenar metadados de documento, seção, versão, data e tipo de conteúdo para permitir filtros e reranking. Se necessário, combinar OCR/layout-aware parsing com revisão manual nas tabelas de maior criticidade.

### 2.2 PDFs escaneados

**Desafio para o pipeline de RAG**

Documentos escaneados exigem OCR, e OCR ruim degrada todo o pipeline seguinte. Erros em números, siglas, datas e títulos de seção afetam tanto a indexação quanto a recuperação.

**Impacto na qualidade das respostas**

O assistente pode deixar de encontrar a informação correta porque os termos-chave foram reconhecidos incorretamente, ou pode usar texto corrompido como evidência. Em conteúdos normativos, isso reduz precisão e confiança justamente onde o sistema deveria ser mais conservador.

**Estratégia de tratamento**

Aplicar OCR com avaliação de qualidade por documento e pipeline de limpeza pós-OCR. Documentos com baixa confiança devem ser marcados para revisão humana ou excluídos temporariamente da base consultável. Também é recomendável guardar um score de confiança do OCR como metadado para reduzir o peso desses chunks no ranking final.

### 2.3 Wiki do Confluence com links e macros

**Desafio para o pipeline de RAG**

A wiki traz conteúdo altamente interligado. Links internos, macros e páginas compostas por blocos dinâmicos dificultam a extração de uma unidade semântica estável. Páginas curtas demais podem depender de contexto externo; páginas longas demais podem reunir assuntos demais.

**Impacto na qualidade das respostas**

Sem preservar relações entre páginas, o assistente pode recuperar um trecho parcialmente correto, mas sem as definições ou exceções necessárias que estavam em outra página vinculada. Isso aumenta respostas incompletas, especialmente em processos operacionais que dependem de navegação entre páginas.

**Estratégia de tratamento**

Extrair o conteúdo com resolução de macros relevantes e capturar metadados de navegação, como título, breadcrumbs, links de origem e área dona do conteúdo. O chunking deve respeitar headings e subtópicos. Para perguntas que dependem de relação entre páginas, vale enriquecer o retrieval com expansão por links ou reranking com contexto vizinho.

### 2.4 Planilhas com fórmulas interdependentes

**Desafio para o pipeline de RAG**

Planilhas não são apenas texto; elas embutem lógica de cálculo. Ler apenas o valor visível ou apenas a fórmula pode ser insuficiente. Além disso, abas diferentes podem depender umas das outras.

**Impacto na qualidade das respostas**

Sem tratamento específico, o sistema pode recuperar uma tabela de referência sem captar as condições de cálculo, ou recuperar uma fórmula sem os parâmetros necessários. Isso é crítico em cenários como frete, descontos e regras tarifárias.

**Estratégia de tratamento**

Converter planilhas para uma representação híbrida: texto explicativo, tabelas normalizadas e metadados de aba/faixa/célula. Para planilhas de negócio críticas, gerar artefatos derivados mais estáveis para indexação, como tabelas achatadas com descrição semântica das fórmulas. Se a planilha for usada para cálculo, o ideal é não confiar só em RAG; a resposta deve consultar uma lógica determinística ou serviço de cálculo complementar.

## 3. Estimativa do tamanho da base em tokens

O enunciado fornece volume de PDFs, páginas wiki e planilhas, além da regra prática de aproximadamente 0,75 palavra por token. Isso implica:

$$
tokens \approx \frac{palavras}{0.75}
$$

Como o exercício não informa a densidade média por página dos PDFs nem o volume textual das planilhas, a estimativa precisa ser assumida explicitamente.

### 3.1 Premissas adotadas

1. PDFs: 800 documentos, média de 10 páginas, com 400 palavras por página em média.
2. Wiki: 400 páginas, média de 1.500 palavras por página.
3. Planilhas: 50 arquivos, estimando 2.000 palavras equivalentes por planilha após extração estruturada básica.

### 3.2 Cálculo

**PDFs**

$$
800 \times 10 \times 400 = 3.200.000 \text{ palavras}
$$

$$
3.200.000 / 0.75 \approx 4.266.667 \text{ tokens}
$$

**Wiki**

$$
400 \times 1.500 = 600.000 \text{ palavras}
$$

$$
600.000 / 0.75 = 800.000 \text{ tokens}
$$

**Planilhas**

$$
50 \times 2.000 = 100.000 \text{ palavras}
$$

$$
100.000 / 0.75 \approx 133.333 \text{ tokens}
$$

**Total aproximado**

$$
3.900.000 \text{ palavras} \approx 5.200.000 \text{ tokens}
$$

### 3.3 Interpretação

A base inteira não cabe nem remotamente em uma única consulta. Mesmo com uma janela de 128K tokens, a arquitetura depende de recuperação seletiva. Também vale destacar que esse número pode variar bastante: PDFs com mais imagens e tabelas densas reduzem a quantidade de palavras por página, enquanto OCR ruidoso pode inflar o texto extraído com baixa utilidade semântica.

## 4. Orçamento de contexto por consulta

Considerando o GPT-4o com janela de 128K tokens e um consumo fixo de aproximadamente 2K tokens para system prompt e instruções:

$$
128.000 - 2.000 = 126.000 \text{ tokens úteis teóricos}
$$

Se cada chunk tiver cerca de 500 tokens:

$$
126.000 / 500 = 252 \text{ chunks teóricos}
$$

Esse número não deve ser interpretado como recomendação prática. Ele representa apenas o teto bruto. Na prática, seria inadequado preencher a janela com centenas de chunks porque ainda há custo de pergunta do usuário, histórico, metadados, instruções de saída e, principalmente, perda de atenção do modelo em contextos longos.

### 4.1 Implicação arquitetural

O problema central não é quantos chunks cabem; é quantos chunks úteis cabem antes que o contexto fique ruidoso. Para esse caso, a estratégia mais segura é recuperar poucos chunks de alta precisão, idealmente entre 5 e 12 chunks fortes, e não 50 ou 100 chunks medianos. Isso reduz conflitos entre versões, diminui o efeito de *lost in the middle* e facilita citação correta de fonte.

### 4.2 Relação com retrieval

O retrieval deve priorizar precisão sobre cobertura bruta. Isso favorece uma abordagem com:

1. Busca híbrida, combinando semântica com termos exatos para nomes de documentos, seções, números e siglas.
2. Filtros por metadados, como tipo documental, data, área responsável, vigência e versão.
3. Reranking para reduzir documentos formalmente parecidos, mas semanticamente inadequados.
4. Regras para desempate entre documentos contraditórios, privilegiando fonte normativa/contratual e versões mais recentes quando a vigência for clara.

## 5. Recomendação de chunking

### 5.1 Estratégia recomendada

O melhor caminho não é chunking fixo cego por tamanho. A recomendação é chunking semântico orientado pela estrutura do documento, com tamanho alvo entre 300 e 600 tokens para texto corrido, overlap moderado de aproximadamente 10% a 15% quando houver dependência entre seções adjacentes, e tratamento especial para tabelas, listas normativas e exceções.

### 5.2 Como isso se aplica ao caso NovaTech

As perguntas do atendimento tendem a ser pontuais: prazo, elegibilidade, multiplicador, tier, SLA, exceção, procedimento. Esse perfil favorece chunks relativamente compactos, autocontidos e ricos em metadados. Se o chunk for grande demais, a informação correta pode ficar diluída; se for pequeno demais, a exceção pode se separar da regra principal.

Exemplos práticos:

1. Políticas e procedimentos: chunk por seção ou subseção, preservando regra principal com suas exceções imediatas.
2. Tabelas de SLA e frete: chunk por tabela inteira se couber com clareza; se não couber, chunk por blocos de linhas mantendo cabeçalho repetido.
3. FAQs e conteúdo informal: chunk separado e explicitamente marcado como fonte de menor autoridade.
4. Documentos versionados: nunca misturar no mesmo chunk conteúdo de versões diferentes; a versão deve virar metadado obrigatório no índice.

### 5.3 Relação com *lost in the middle*

Mesmo quando a janela comporta muito contexto, informação colocada no meio de prompts longos tende a receber menos atenção. Por isso, não basta recuperar o chunk correto; é necessário ordenar o contexto com intenção. Os chunks mais relevantes e mais confiáveis devem aparecer primeiro. Chunks complementares ou de menor autoridade devem vir depois, e apenas quando realmente ajudarem a responder.

Uma consequência direta para a NovaTech é que documentos normativos e contratuais devem ter precedência sobre FAQ informal. Também é recomendável inserir, antes dos chunks, um cabeçalho curto explicando a prioridade das fontes, para reduzir a chance de o modelo combinar evidências conflitantes como se fossem equivalentes.

## 6. Riscos principais

1. Mistura entre PROC-042 e PROC-042-v2 no mesmo contexto, gerando respostas contraditórias.
2. Uso excessivo de FAQ informal como evidência primária em temas críticos.
3. OCR ruim degradando embeddings e empurrando chunks errados para o topo.
4. Planilhas indexadas como texto puro sem preservar a lógica de cálculo.
5. Excessiva confiança na janela de contexto, em vez de investir em boa seleção e ordenação do contexto.

## 7. Conclusão

O projeto é viável, mas depende de um pipeline mais disciplinado do que uma solução genérica de RAG. A combinação correta é: ingestão multimodal com tratamento específico por tipo de fonte, chunking semântico com preservação de estrutura, metadados fortes para governança de versões e autoridade documental, retrieval híbrido com reranking e uma política explícita de priorização de fontes no prompt.

Em outras palavras, o assistente da NovaTech não falhará por falta de modelo; ele falhará se receber contexto ruim, conflitante ou mal posicionado. Por isso, a engenharia de contexto é parte central da arquitetura, não um detalhe de implementação.

## 8. Próxima etapa sugerida

Submeter esta versão ao Claude pedindo revisão crítica com foco em três pontos: premissas otimistas demais, riscos operacionais ignorados e fragilidades na estratégia de chunking/retrieval. O entregável final deve manter o histórico dessa iteração.