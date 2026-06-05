# Exercício 1.2 — System Prompt v1

## 1. System Prompt v1

```text
Você é o assistente interno de atendimento da NovaTech.

Seu objetivo é responder perguntas de atendentes com base exclusivamente nos chunks de documentação fornecidos na conversa atual.

Você atua em um cenário de suporte operacional e deve priorizar precisão, rastreabilidade e segurança da informação. Quando houver informação insuficiente, incompleta ou ausente nos chunks fornecidos, você deve reconhecer explicitamente essa limitação em vez de preencher lacunas com suposições.

IDENTIDADE E OBJETIVO
- Você responde dúvidas operacionais sobre políticas, SLAs, frete e procedimentos da NovaTech.
- Você deve ajudar o atendente a responder rápido, mas sem sacrificar precisão.
- Você não é autorizado a usar conhecimento externo, memória implícita ou inferências que extrapolem o que está documentado nos chunks disponíveis.

REGRAS INVIOLÁVEIS
1. Use apenas informações presentes nos chunks fornecidos.
2. Sempre cite a fonte do documento usado na resposta, mencionando nome do documento e seção quando essa informação estiver disponível no chunk.
3. Nunca invente prazo, valor, multiplicador, regra, exceção, processo ou contato que não esteja explicitamente presente nos chunks.
4. Se a informação disponível for insuficiente para responder completamente, diga isso de forma explícita.
5. Quando houver informação parcial útil, forneça apenas a parte que está suportada pelos chunks e sinalize claramente o que está faltando.
6. Se não encontrar resposta suficiente, recomende escalar para o supervisor.
7. Responda em português formal, claro e acessível.

PRIORIDADE DE DECISÃO
Ao responder, siga esta ordem:
1. Verifique se algum chunk responde diretamente à pergunta.
2. Se houver regra geral e exceção no mesmo contexto, priorize a exceção.
3. Se a pergunta exigir dado numérico ou parâmetro que não aparece nos chunks, não calcule nem estime o resultado final.
4. Se houver apenas resposta parcial, entregue apenas a resposta parcial com ressalva explícita.
5. Nunca trate ausência de dado como autorização para completar com hipótese.

USO DOS CHUNKS
- Considere os chunks como a única base de verdade disponível nesta interação.
- Não misture informações de chunks diferentes se eles tratarem de assuntos distintos e a pergunta não exigir os dois.
- Não reaproveite informações irrelevantes só porque elas estão presentes no contexto.
- Se a pergunta mencionar um caso específico, responda apenas com o chunk que efetivamente sustenta esse caso.
- Se um chunk contiver uma exceção explícita, ela prevalece sobre a regra geral.

REGRAS PARA DADOS INCOMPLETOS
- Se faltar um elemento essencial para concluir a resposta, diga exatamente o que falta.
- Se a pergunta pedir um valor final e os chunks trouxerem apenas fórmula ou parâmetros parciais, explique que não é possível calcular o valor final com segurança.
- Se a pergunta não puder ser respondida com base suficiente, informe que a documentação disponível não traz a resposta completa e sugira escalar para o supervisor.

FORMATO DE RESPOSTA
Responda sempre neste formato:

1. Resposta objetiva: responda primeiro à pergunta de forma direta.
2. Base documental: explique a resposta usando apenas o conteúdo suportado pelos chunks.
3. Fonte: cite o documento e a seção.
4. Próximo passo: se faltarem dados ou houver limitação, diga o que precisa ser feito.

EXEMPLOS DE COMPORTAMENTO ESPERADO
- Se a pergunta trouxer uma exceção, não responda apenas com a regra geral.
- Se a pergunta pedir um cálculo sem valor base, não invente o número final.
- Se a pergunta pedir um prazo e o chunk indicar que o caso está excluído da regra geral, responda com a exclusão, não com o prazo padrão.

CRITÉRIO FINAL DE QUALIDADE
É melhor responder de forma parcial e correta do que responder de forma completa e incorreta.
```

## 2. Intenção desta v1

Esta primeira versão do prompt foi escrita para maximizar três comportamentos:

1. Fazer o modelo respeitar o contexto recuperado como única fonte de verdade.
2. Fazer o modelo priorizar exceções sobre regras gerais.
3. Fazer o modelo falhar corretamente quando faltarem dados, especialmente em perguntas de cálculo.

## 3. O que esta v1 deve ser capaz de fazer bem

Com os 3 chunks do enunciado, esta v1 deve tender a produzir estes comportamentos:

1. Para carga perigosa, responder que a exceção impede aplicar o prazo padrão de 7 dias.
2. Para cliente Gold, distinguir corretamente SLA de resolução de SLA de primeira resposta.
3. Para frete de 600kg para Manaus, recusar cálculo final por falta do valor base e responder apenas com a informação parcial suportada.

## 4. Risco esperado nesta v1

Mesmo com essas regras, ainda existe risco de o modelo:

1. Repetir informações desnecessárias do chunk junto da resposta principal.
2. Produzir respostas longas demais para perguntas simples.
3. Não explicitar com clareza suficiente a diferença entre resposta parcial e ausência total de resposta.

Esses pontos devem ser verificados nos testes com o Claude e, se necessário, corrigidos no `system prompt v2`.

## 5. Mapeamento de contexto estático e dinâmico

### 5.1 Contexto estático

Nesta solução, entram como contexto estático os elementos que deveriam acompanhar toda consulta:

1. Identidade do assistente interno da NovaTech.
2. Objetivo do assistente no cenário de atendimento.
3. Regras invioláveis de uso exclusivo dos chunks.
4. Prioridade de decisão entre regra direta, exceção e dado ausente.
5. Formato obrigatório de resposta.
6. Instruções sobre resposta parcial, ausência de resposta e escalonamento.

Em termos aproximados, esse bloco tem entre 500 e 800 tokens, dependendo da formatação final e da verbosidade do modelo ao serializar o prompt.

### 5.2 Contexto dinâmico

Mudam a cada interação:

1. Os chunks efetivamente recuperados pelo RAG naquela pergunta.
2. A pergunta do atendente.
3. Eventuais dados adicionais do caso, se existirem.
4. Histórico relevante da conversa, se houver.

No teste simplificado do exercício, o contexto dinâmico é pequeno. Os três chunks juntos devem ficar em algo próximo de 150 a 250 tokens, e cada pergunta do usuário fica tipicamente abaixo de 20 tokens.

### 5.3 Orçamento de contexto neste exercício

O ponto importante aqui não é limite de janela, e sim disciplina de escopo. Mesmo com contexto curto, o assistente só deveria usar os três chunks do enunciado durante o teste.

Em termos práticos:

1. Contexto estático: aproximadamente 500 a 800 tokens.
2. Contexto dinâmico do teste: aproximadamente 170 a 270 tokens.
3. Total por consulta: aproximadamente 700 a 1.100 tokens.

Ou seja, o exercício não pressiona a janela de contexto. Ele pressiona a capacidade do prompt de impedir extrapolação indevida.

## 6. Teste v1 com respostas reais

As três perguntas aplicadas ao prompt v1 foram estas:

1. "Qual o prazo de devolução para carga perigosa?"
2. "Meu cliente é Gold, qual o SLA de resolução?"
3. "Quanto custa o frete para 600kg para Manaus?"

As respostas obtidas foram documentadas abaixo porque o exercício pede teste real, não apenas expectativa teórica.

### 6.1 Pergunta 1: carga perigosa

**Resposta obtida**

O modelo respondeu que não se aplica o prazo padrão de 7 dias úteis, afirmou que carga perigosa não é elegível para devolução pelo processo padrão e orientou encaminhamento ao setor de Gestão de Riscos no ramal 4500.

**O que acertou**

1. Priorizou corretamente a exceção sobre a regra geral.
2. Não respondeu incorretamente "7 dias úteis".
3. Manteve a ideia de que não existe prazo padrão aplicável ao caso.

**O que desviou do exercício**

1. Trouxe o contato do setor de Gestão de Riscos, que não está presente no chunk simplificado do enunciado.
2. Citou as seções 3.1 e 3.2 do documento completo, quando o exercício pede operar só com os chunks fornecidos.

**Diagnóstico**

A resposta está na direção correta do ponto de vista factual, mas falha no protocolo do teste. O exercício mede se o assistente consegue se limitar ao chunk disponível. Aqui houve contaminação pelo corpus ampliado, o que torna a resposta menos auditável para o cenário controlado.

### 6.2 Pergunta 2: SLA de resolução para cliente Gold

**Resposta obtida**

O modelo respondeu que cliente Gold tem SLA de resolução de até 24 horas úteis em chamados gerais e de até 4 horas em incidentes críticos, pedindo que o usuário confirmasse o tipo de chamado.

**O que acertou**

1. Não confundiu resolução com primeira resposta.
2. Manteve o valor de 24 horas úteis como prazo de resolução para chamados gerais.

**O que desviou do exercício**

1. Introduziu a distinção entre chamados gerais e incidentes críticos, que não existe no chunk B do enunciado.
2. Transformou uma pergunta direta, que tinha resposta suficiente no chunk, em uma resposta condicional desnecessária.

**Diagnóstico**

A resposta mostra conhecimento documental maior do que o permitido pelo teste. No exercício, o comportamento esperado é responder diretamente "até 24h" com base na tabela fornecida. Ao expandir para uma categoria que não estava no chunk, o modelo não inventou um fato, mas extrapolou o contexto permitido.

### 6.3 Pergunta 3: frete para 600kg em Manaus

**Resposta obtida**

O modelo respondeu que não era possível calcular o valor final sem o valor base, informou que Manaus pertence à região Norte, citou multiplicador regional de 1,8 e acrescentou que para 600kg o fator de peso seria 1,0.

**O que acertou**

1. Recusou corretamente o cálculo final por falta do valor base.
2. Indicou corretamente que Manaus está na região Norte.
3. Manteve o multiplicador regional de 1,8, que é suportado pelo chunk C.

**O que desviou do exercício**

1. Introduziu fator de peso 1,0, informação que não existe no chunk C fornecido no teste.
2. Citou a seção 2.1 do documento completo, embora o cenário controlado tenha apenas um chunk resumido.

**Diagnóstico**

A resposta acertou o principal guardrail, que era não inventar o valor final. Ainda assim, extrapolou o contexto ao completar a fórmula com um parâmetro ausente no chunk. Esse é o exemplo mais claro de por que o v2 precisa proibir explicitamente a importação de detalhes de documentos correlatos não presentes na conversa atual.

## 7. Síntese da avaliação do v1

O v1 acertou a intenção central nas três perguntas:

1. Priorizou exceção sobre regra geral.
2. Diferenciou corretamente resolução de primeira resposta.
3. Falhou corretamente no cálculo final por falta de dado essencial.

Mas o v1 não controlou um comportamento crítico para o exercício: o modelo respondeu com base no corpus ampliado, e não apenas nos três chunks do teste.

Portanto, a falha principal do v1 não foi factual. Foi de governança de contexto.

## 8. System Prompt v2

```text
Você é o assistente interno de atendimento da NovaTech.

Seu objetivo é responder perguntas de atendentes com base exclusivamente nos chunks de documentação fornecidos na conversa atual.

Você atua em um cenário de suporte operacional e deve priorizar precisão, rastreabilidade e segurança da informação. Quando houver informação insuficiente, incompleta ou ausente nos chunks fornecidos, você deve reconhecer explicitamente essa limitação em vez de preencher lacunas com suposições.

IDENTIDADE E OBJETIVO
- Você responde dúvidas operacionais sobre políticas, SLAs, frete e procedimentos da NovaTech.
- Você deve ajudar o atendente a responder rápido, mas sem sacrificar precisão.
- Você não é autorizado a usar conhecimento externo, memória implícita, partes não exibidas do documento nem inferências que extrapolem o que está documentado nos chunks disponíveis nesta conversa.

REGRAS INVIOLÁVEIS
1. Use apenas informações literalmente presentes nos chunks fornecidos nesta interação.
2. Sempre cite a fonte do chunk usado na resposta, mencionando nome do documento e seção quando essa informação estiver disponível no próprio chunk.
3. Nunca invente prazo, valor, multiplicador, regra, exceção, processo, contato ou parâmetro que não esteja explicitamente presente nos chunks.
4. Se a informação disponível for insuficiente para responder completamente, diga isso de forma explícita.
5. Quando houver informação parcial útil, forneça apenas a parte que está suportada pelos chunks e sinalize claramente o que está faltando.
6. Se não encontrar resposta suficiente, recomende escalar para o supervisor.
7. Responda em português formal, claro e acessível.

REGRAS DE ESCOPO
1. Trate os chunks exibidos na conversa como a única base de verdade disponível neste turno.
2. Não complemente a resposta com trechos de outras seções, outras versões, outros documentos ou conhecimento prévio, mesmo que pareçam relacionados ao tema.
3. Se a pergunta parecer simples e um chunk já contiver a resposta direta, responda apenas com essa resposta direta, sem abrir cenários alternativos não mencionados no chunk.
4. Se uma fórmula estiver incompleta nos chunks, não complete os parâmetros ausentes com memória ou com documentos correlatos. Responda apenas com a parte documentada.
5. Se um chunk trouxer uma exceção explícita, essa exceção prevalece sobre a regra geral.

PRIORIDADE DE DECISÃO
Ao responder, siga esta ordem:
1. Verifique se algum chunk responde diretamente à pergunta.
2. Se houver regra geral e exceção no mesmo contexto, priorize a exceção.
3. Se a pergunta exigir dado numérico ou parâmetro que não aparece nos chunks, não calcule nem estime o resultado final.
4. Se houver apenas resposta parcial, entregue apenas a resposta parcial com ressalva explícita.
5. Nunca trate ausência de dado como autorização para completar com hipótese.

REGRAS PARA DADOS INCOMPLETOS
- Se faltar um elemento essencial para concluir a resposta, diga exatamente o que falta.
- Se a pergunta pedir um valor final e os chunks trouxerem apenas fórmula ou parâmetros parciais, explique que não é possível calcular o valor final com segurança.
- Se a pergunta não puder ser respondida com base suficiente, informe que a documentação disponível não traz a resposta completa e sugira escalar para o supervisor.

FORMATO DE RESPOSTA
Responda sempre neste formato:

1. Resposta objetiva: responda primeiro à pergunta de forma direta e sem expandir para cenários não pedidos.
2. Base documental: explique a resposta usando apenas o conteúdo suportado pelos chunks.
3. Fonte: cite o documento e a seção quando estiverem presentes no chunk.
4. Próximo passo: se faltarem dados ou houver limitação, diga o que precisa ser feito.

CRITÉRIO FINAL DE QUALIDADE
É melhor responder de forma curta, parcial e correta do que responder de forma completa com detalhes que não aparecem nos chunks atuais.
```

## 9. O que mudou do v1 para o v2

As mudanças não são cosméticas. Elas atacam exatamente os desvios observados no teste:

1. O v2 proíbe explicitamente usar partes não exibidas do documento ou do corpus ampliado.
2. O v2 manda responder de forma direta quando o chunk já resolve a pergunta, evitando abrir cenários laterais não pedidos.
3. O v2 proíbe completar fórmulas com parâmetros ausentes, mesmo que pareçam óbvios a partir de documentos correlatos.
4. O v2 reforça que a citação só vale para o que está presente no próprio chunk, e não para consulta implícita ao documento completo.

## 10. Teste v2

As mesmas três perguntas foram reaplicadas ao v2:

1. "Qual o prazo de devolução para carga perigosa?"
2. "Meu cliente é Gold, qual o SLA de resolução?"
3. "Quanto custa o frete para 600kg para Manaus?"

### 10.1 Critério de sucesso esperado

**Pergunta 1**

Sucesso se o modelo responder que a carga perigosa está fora do processo padrão ou que a exceção impede aplicar o prazo geral, sem inventar contato, ramal ou procedimento adicional ausente no chunk.

**Pergunta 2**

Sucesso se o modelo responder diretamente "até 24h" e citar SLA-2024, sem introduzir distinções ausentes no chunk.

**Pergunta 3**

Sucesso se o modelo disser que não é possível calcular o valor final sem o valor base, citar PROC-042-v2, mencionar que Manaus está na região Norte e que o multiplicador regional é 1,8, sem acrescentar fatores ou regras ausentes no chunk.

### 10.2 Resultados reais do v2

**Pergunta 1: carga perigosa**

**Resposta obtida**

O modelo respondeu que não era possível informar com segurança o prazo de devolução para carga perigosa porque, segundo ele, nenhum chunk documental sobre esse tema teria sido fornecido na interação.

**O que acertou**

1. Não inventou prazo, exceção ou procedimento sem base explícita.
2. Manteve postura conservadora diante da percepção de contexto insuficiente.

**O que desviou do exercício**

1. Falhou em usar o chunk de teste esperado para a pergunta sobre devolução e carga perigosa.
2. Recuou para ausência total de resposta quando a expectativa do exercício era uma resposta parcial, mas suficiente, priorizando a exceção.

**Diagnóstico**

Houve regressão em relação ao comportamento esperado. O v2 corrigiu a extrapolação do corpus ampliado, mas ficou rígido demais e passou a agir como se não tivesse acesso ao chunk recuperado do teste. Em vez de responder com a exceção documentada, respondeu como se a evidência não existisse.

**Pergunta 2: SLA de resolução para cliente Gold**

**Resposta obtida**

O modelo respondeu que o SLA de resolução para cliente Gold é de até 24 horas úteis.

**O que acertou**

1. Respondeu diretamente o valor correto esperado no exercício.
2. Não confundiu SLA de resolução com SLA de primeira resposta.
3. Não introduziu categorias adicionais ausentes no chunk.

**O que desviou do exercício**

1. A base documental faz referência ao conteúdo esperado do chunk, mas não cita uma seção específica.
2. O próximo passo ainda abre a possibilidade de consultar exceções não presentes no contexto do teste, embora isso seja um desvio pequeno.

**Diagnóstico**

Esta foi a melhor resposta do v2. Ela ficou muito mais alinhada ao exercício do que a resposta correspondente do v1, porque entregou a resposta direta esperada sem puxar distinções extras do corpus ampliado.

**Pergunta 3: frete para 600kg em Manaus**

**Resposta obtida**

O modelo respondeu que não era possível calcular o valor final sem o valor base, afirmou que Manaus está na região Norte e informou multiplicador regional de 1,8.

**O que acertou**

1. Recusou corretamente o cálculo final por falta do valor base.
2. Mencionou apenas os elementos efetivamente suportados pelo chunk de teste.
3. Não completou a fórmula com fator de peso ausente no contexto.

**O que desviou do exercício**

1. A fonte foi citada de forma genérica, sem seção.
2. O próximo passo fala em consultar o valor base previsto no procedimento, formulação aceitável, mas menos precisa do que explicitar que o dado não apareceu no chunk atual.

**Diagnóstico**

O v2 corrigiu exatamente o principal desvio do v1 nesta pergunta. A resposta permaneceu parcial, mas agora ficou dentro dos limites do contexto permitido e não importou parâmetros adicionais.

### 10.3 Tabela de comparação preenchida

| Pergunta | Resultado esperado | Resultado real v2 | Status |
|---------|--------------------|-------------------|--------|
| Carga perigosa | Prioriza exceção sem inventar procedimento adicional | Declarou ausência de chunk e não respondeu a exceção | Falhou |
| SLA Gold | Responde diretamente até 24h | Respondeu diretamente até 24 horas úteis | Passou |
| Frete 600kg Manaus | Responde parcialmente sem completar parâmetros ausentes | Respondeu parcialmente sem completar parâmetros ausentes | Passou |

### 10.4 Leitura comparativa entre v1 e v2

Comparando as duas versões:

1. O v2 melhorou claramente na pergunta sobre SLA Gold, porque deixou de abrir cenários ausentes no chunk.
2. O v2 também melhorou na pergunta sobre frete, porque deixou de completar a fórmula com parâmetro inexistente no contexto do teste.
3. O v2 piorou na pergunta sobre carga perigosa, porque trocou uma resposta parcial correta por uma recusa indevida baseada em ausência de chunk.

Isso mostra que a iteração resolveu a extrapolação de contexto, mas introduziu um novo risco: o modelo pode interpretar as regras de escopo de forma tão restritiva que deixa de usar o chunk correto mesmo quando ele deveria estar disponível no cenário de teste.

## 11. Reflexão final

O v1 já indicava uma boa direção de comportamento, mas não era auditável para o exercício porque deixava o modelo ampliar a base consultada sem sinalizar isso. O v2 atacou esse problema de forma concreta e melhorou em dois dos três testes: eliminou a expansão indevida na resposta sobre SLA Gold e deixou de completar a fórmula de frete com parâmetro ausente.

Ao mesmo tempo, o teste v2 revelou uma nova fragilidade importante. As regras de escopo ficaram severas o bastante para induzir uma recusa indevida na pergunta sobre carga perigosa. Em vez de usar a exceção presente no chunk esperado do teste, o modelo se comportou como se não houvesse evidência disponível. Isso sugere que a próxima iteração do prompt precisa equilibrar melhor dois objetivos: impedir extrapolação fora do contexto e, ao mesmo tempo, obrigar o uso afirmativo do chunk quando ele de fato responde à pergunta.

Em outras palavras, a v2 melhorou a disciplina de contexto, mas ainda não fechou o comportamento ideal. A v3 deveria acrescentar uma instrução do tipo: "quando houver chunk suficiente para responder, não trate o contexto como ausente". Esse ajuste tende a preservar os ganhos do v2 sem perder a capacidade de responder corretamente à exceção da carga perigosa.