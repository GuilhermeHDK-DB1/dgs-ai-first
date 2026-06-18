# Tasks — Query Endpoint

Derivado de: `specs/query-endpoint/plan.md`  
Estimativas: P = Pequeno (< 2h) | M = Médio (2-4h) | G = Grande (> 4h)

---

## T-001 — Instalar dependências de produção

**Estimativa:** P  
**Dependências:** —

**Descrição:**  
Adicionar ao `package.json` as dependências de produção: `@azure/functions` v4, `pino`, `@azure/search-documents`, `@azure/openai`.

**Critérios de aceite:**
- `package.json` contém os 4 pacotes em `dependencies` (não `devDependencies`)
- `npm install` executa sem erros
- `tsc --noEmit` compila sem erros

---

## T-002 — Definir tipos TypeScript compartilhados

**Estimativa:** P  
**Dependências:** T-001

**Descrição:**  
Criar `src/shared/types.ts` com os tipos de domínio usados em toda a aplicação.

**Critérios de aceite:**
- Exporta `QueryRequest`, `QueryResponse`, `Chunk`, `SearchResult`
- `Chunk` inclui campo `vigencia?: string` (rastreabilidade ADR-0003)
- TypeScript strict mode passa sem erros; nenhum tipo `any` presente

---

## T-003 — Implementar módulo de config de ambiente

**Estimativa:** P  
**Dependências:** T-001

**Descrição:**  
Criar `src/shared/config.ts` que lê variáveis de ambiente obrigatórias e lança erro descritivo na startup.

**Critérios de aceite:**
- Lê `AZURE_OPENAI_ENDPOINT`, `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_INDEX_NAME`, `AZURE_OPENAI_DEPLOYMENT_NAME`
- Lança `Error("Missing required env var: NOME_DA_VAR")` para qualquer var ausente
- Nenhum valor hardcoded (sem URLs ou keys inline)
- Unit test: processo com var faltante lança o erro esperado

---

## T-004 — Implementar logger estruturado com pino

**Estimativa:** P  
**Dependências:** T-001

**Descrição:**  
Criar `src/shared/logger.ts` exportando instância pino configurada para logging estruturado.

**Critérios de aceite:**
- Exporta instância pino com `level` via env `LOG_LEVEL` (default: `"info"`)
- Nenhum `console.log` ou `console.error` em nenhum arquivo de `src/`
- Log inclui campo `requestId` quando disponível no contexto

---

## T-005 — Implementar validador de input do endpoint

**Estimativa:** P  
**Dependências:** T-002

**Descrição:**  
Criar `src/functions/query/validator.ts` com schema Zod para `QueryRequest`.

**Critérios de aceite:**
- Valida `{ question: string }` com mínimo 1 char não-espaço e máximo 500
- `safeParse({ question: "   " })` retorna `success: false` (strings só-espaço rejeitadas)
- Retorna tipo discriminado `{ success: true; data: QueryRequest } | { success: false; errors: ValidationError[] }`
- Cada `ValidationError` tem forma `{ error: "validation_error"; field: string; message: string }`
- Tipo `QueryRequest` exportado via `z.infer<typeof QueryRequestSchema>`

---

## T-006 — Implementar HTTP trigger do query endpoint

**Estimativa:** S  
**Dependências:** T-003, T-004, T-005

**Descrição:**  
Implementar `src/functions/query/handler.ts` como Azure Function v4 HTTP trigger.

**Critérios de aceite:**
- Registrado com `app.http("query", { route: "query", methods: ["POST"] })`
- Retorna `400` com `errors: ValidationError[]` para input inválido
- Retorna `501 Not Implemented` para input válido (stub até T-012)
- Unit test com mock de `HttpRequest` passa para input válido e inválido sem credenciais Azure

---

## T-007 — Implementar custom errors

**Estimativa:** P  
**Dependências:** T-001

**Descrição:**  
Criar `src/shared/errors.ts` com hierarquia de erros do domínio.

**Critérios de aceite:**
- Define `AppError` (base) com `statusCode: number` e `requestId?: string`
- Define `ValidationError`, `SearchError`, `CompletionError` estendendo `AppError`
- Status codes padrão: ValidationError=400, SearchError=502, CompletionError=502
- Unit test: `new SearchError("timeout")` tem `statusCode === 502`

---

## T-008 — Implementar integração Azure AI Search

**Estimativa:** M  
**Dependências:** T-002, T-003, T-007

**Descrição:**  
Criar `src/services/search.ts` com busca vetorial de top-5 chunks.

**Critérios de aceite:**
- Retorna `Chunk[]` (máx. 5) para um vetor de embedding
- Retry exponential backoff (1s → 2s → 4s) em erros 5xx
- Lança `SearchError` após 3 tentativas falhas
- Unit test com mock do `@azure/search-documents` SDK passa sem chamadas reais ao Azure

---

## T-009 — Implementar geração de embedding

**Estimativa:** M  
**Dependências:** T-002, T-003, T-007

**Descrição:**  
Implementar em `src/services/completion.ts` a geração de embeddings via Azure OpenAI.

**Critérios de aceite:**
- Retorna `number[]` (vetor de embedding) para um texto de entrada
- Retry em resposta 429 (rate limit) com exponential backoff
- Lança `CompletionError` após falha definitiva
- Unit test com mock do `@azure/openai` SDK passa

---

## T-010 — Implementar prompt builder com context budget

**Estimativa:** S  
**Dependências:** T-002

**Descrição:**  
Criar `src/services/prompt-builder.ts` que monta o prompt respeitando o budget da ADR-0002.

**Critérios de aceite:**
- Lê `prompts/system-prompt.md` do sistema de arquivos
- System prompt ocupa ≤ 4.000 tokens (estimativa: ~4 chars/token)
- Chunks incluídos somam ≤ 8.000 tokens; chunks com `vigencia` mais recente têm prioridade (ADR-0003)
- Unit test: com 10 chunks de 1.500 tokens cada, apenas os primeiros 5 são incluídos

---

## T-011 — Implementar chamada GPT-4o e montar resposta

**Estimativa:** S  
**Dependências:** T-009, T-010, T-007

**Descrição:**  
Completar `src/services/completion.ts` com chamada de completion e montagem da `QueryResponse`.

**Critérios de aceite:**
- Retorna `QueryResponse` com `answer` e `sourceDocuments: string[]` únicos
- `sourceDocuments` lista os valores `sourceDocument` dos chunks usados no prompt
- Retry em 429 com exponential backoff
- Unit test com mock passa; `sourceDocuments` está populado corretamente

---

## T-012 — Integrar pipeline completo no endpoint

**Estimativa:** M  
**Dependências:** T-006, T-008, T-009, T-010, T-011

**Descrição:**  
Substituir o stub `501` em `handler.ts` pelo pipeline completo.

**Critérios de aceite:**
- POST /api/query retorna `200` com `{ answer: string; sourceDocuments: string[] }`
- Erros do pipeline retornam `502` com `{ error: string; requestId: string }`
- Teste de integração (Azure mockado via MSW ou vitest mock) retorna resposta com `sourceDocuments` populado
- Nenhum `console.log` no código final
