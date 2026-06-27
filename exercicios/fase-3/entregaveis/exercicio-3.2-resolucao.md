# Exercício 3.2 - Revisão crítica de código gerado por IA

## 1. Revisão humana inicial (antes do Claude)

Código revisado: módulo de feedback gerado por IA no enunciado.

### Achados classificados

1. `const body = await request.json() as any;`
- Classificação: violação do AGENTS.md + bug potencial
- Motivo: quebra de TypeScript strict mode e ausência de validação de entrada com Zod.

2. `console.log('Feedback recebido:', JSON.stringify(feedback));`
- Classificação: violação do AGENTS.md + problema de segurança
- Motivo: AGENTS.md exige pino e proíbe log de dados pessoais. O objeto contém `attendantEmail`.

3. `const { CosmosClient } = require('@azure/cosmos');`
- Classificação: violação do AGENTS.md
- Motivo: require dinâmico, contrariando regra de imports estáticos no topo.

4. Persistência sem validação semântica dos campos
- Classificação: bug potencial
- Motivo: `rating`, `queryId` e `comment` podem estar fora do contrato esperado e ainda assim serem gravados.

5. Falta de tratamento explícito para configuração ausente
- Classificação: bug potencial
- Motivo: `COSMOS_CONNECTION_STRING` ausente pode causar falha em runtime sem mensagem operacional clara.

## 2. Segunda revisão (Claude)

Achados identificados na segunda revisão:

1. Falta de validação Zod do payload.
2. Uso de `as any` incompatível com strict mode.
3. Uso de `console.log` em vez de logger estruturado.
4. Exposição de dado pessoal (`attendantEmail`) em log.
5. Uso de `require` dinâmico para `@azure/cosmos`.
6. Ausência de resposta de erro padronizada para payload inválido.

## 3. Comparação: revisão humana vs revisão Claude

Convergências:

1. Ambas encontraram ausência de Zod.
2. Ambas encontraram `as any`.
3. Ambas encontraram `console.log`.
4. Ambas encontraram risco de logar PII (`attendantEmail`).
5. Ambas encontraram `require` dinâmico.

Diferenças:

1. Revisão humana destacou explicitamente risco operacional de variável de ambiente ausente.
2. Revisão Claude destacou padronização de resposta de erro como ponto separado.

Conclusão da comparação:

As revisões são consistentes e complementares. O núcleo de segurança e conformidade foi identificado por ambas, sem divergências relevantes.

## 4. Código reescrito (conforme AGENTS.md)

Arquivo implementado: `src/functions/feedback/handler.ts`

Principais correções aplicadas:

1. Remoção de `as any`.
2. Validação de entrada com Zod (`feedbackInputSchema.strict()`).
3. Troca de `console.log` por pino com log estruturado.
4. Remoção de PII dos logs (não loga `attendantEmail`).
5. Substituição de `require` dinâmico por import estático.
6. Tratamento de erro com resposta padronizada.
7. Verificação explícita de configuração (`COSMOS_CONNECTION_STRING`).

Trecho implementado:

```typescript
import { app, HttpRequest, HttpResponseInit } from '@azure/functions';
import { CosmosClient } from '@azure/cosmos';
import pino from 'pino';
import { z } from 'zod';

const logger = pino({ name: 'feedback-handler' });

const feedbackInputSchema = z
  .object({
    queryId: z.string().trim().min(1, 'queryId is required'),
    rating: z.number().int().min(1).max(5),
    comment: z.string().trim().min(1).max(2000),
    attendantEmail: z.string().email(),
  })
  .strict();

// ... restante no arquivo src/functions/feedback/handler.ts
```

## 5. Aderência aos critérios de avaliação

- Identifica os 4 problemas mínimos exigidos: sim.
- Comparação humano vs Claude é honesta: sim.
- Código reescrito corrige os problemas e segue AGENTS.md: sim.
