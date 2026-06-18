# Exercício 2.2 — Implementação de spec com Spec Driven Development

**Papel:** Desenvolvedor Sênior  
**Ferramentas utilizadas:** GitHub Copilot (tasks.md + código) + Claude (revisão crítica)  
**Repositório:** `D:/novatech-assistant`

---

## 1. `tasks.md` — Decomposição atômica do plan.md (Tarefa 1)

O `plan.md` foi gravado em `specs/query-endpoint/plan.md` e decomposto em 12 tasks atômicas em `specs/query-endpoint/tasks.md`.

**Critério de atomicidade aplicado:** cada task pode ser implementada e testada de forma independente, sem depender de serviços externos não mockados.

**Resumo das tasks:**

| ID | Descrição | Est | Deps | Testável sem Azure? |
|---|---|---|---|---|
| T-001 | Instalar dependências de produção | P | — | ✅ (`npm install`) |
| T-002 | Definir tipos TypeScript compartilhados | P | T-001 | ✅ (`tsc --noEmit`) |
| T-003 | Implementar módulo de config de ambiente | P | T-001 | ✅ (unit test, env mockado) |
| T-004 | Implementar logger estruturado com pino | P | T-001 | ✅ (unit test) |
| **T-005** | **Implementar validador de input do endpoint** | **P** | **T-002** | **✅ (Vitest local)** |
| T-006 | Implementar HTTP trigger do endpoint | S | T-003, T-004, T-005 | ✅ (mock HttpRequest) |
| T-007 | Implementar custom errors | P | T-001 | ✅ (unit test) |
| T-008 | Implementar integração Azure AI Search | M | T-002, T-003, T-007 | ✅ (mock SDK) |
| T-009 | Implementar geração de embedding | M | T-002, T-003, T-007 | ✅ (mock SDK) |
| T-010 | Implementar prompt builder com context budget | S | T-002 | ✅ (unit test) |
| T-011 | Implementar chamada GPT-4o e montar resposta | S | T-009, T-010, T-007 | ✅ (mock SDK) |
| T-012 | Integrar pipeline completo no endpoint | M | T-006..T-011 | ✅ (MSW ou vitest mock) |

**Grafo de dependências:**

```
T-001 ──► T-002 ──► T-005 ──┐
       ├─► T-003 ────────────┼──► T-006 ──┐
       ├─► T-004 ────────────┘             │
       └─► T-007 ──► T-008 ──────────────┐ │
                  └─► T-009 ──► T-011 ───┼─┼──► T-012
          T-002 ──► T-010 ──────────────┘ │
                                          └──────────┘
```

**Por que T-005 é a primeira task implementada com Copilot?**  
É a única task que: (a) não requer credenciais Azure, (b) tem critério de aceite verificável com `tsc` + Vitest localmente, (c) demonstra Zod — biblioteca central de validação do projeto — e (d) desbloqueia T-006 (HTTP trigger).

---

## 2. Código implementado com Copilot (Tarefa 2)

### T-002 — `src/shared/types.ts`

Tipos de domínio compartilhados. Inclui `vigencia?: string` no `Chunk` para suporte à priorização ADR-0003.

```typescript
export interface QueryRequest {
  question: string;
  conversationId?: string;
}

export interface Chunk {
  id: string;
  content: string;
  sourceDocument: string;
  vigencia?: string; // ISO date — priorização ADR-0003
  score: number;
}

export interface SearchResult {
  chunks: Chunk[];
  totalCount: number;
}

export interface QueryResponse {
  answer: string;
  sourceDocuments: string[];
  conversationId?: string;
}
```

### T-005 — `src/functions/query/validator.ts`

**Gerado pelo Copilot (versão original antes da revisão):**

```typescript
import { z } from "zod";

export const QueryRequestSchema = z.object({
  question: z.string().min(1).max(500),
});

export type QueryRequest = z.infer<typeof QueryRequestSchema>;

export function validateQueryRequest(body: unknown) {
  return QueryRequestSchema.safeParse(body);
}
```

**Versão corrigida após revisão crítica (ver Seção 3):**

```typescript
import { z } from "zod";

export const QueryRequestSchema = z.object({
  question: z
    .string()
    .trim()                                    // FIX #1: rejeita strings só-espaço
    .min(1, "Question cannot be empty")
    .max(500, "Question cannot exceed 500 characters"),
  conversationId: z.string().uuid().optional(),
});

export type QueryRequest = z.infer<typeof QueryRequestSchema>;

export interface ValidationError {            // FIX #2: shape estruturado
  error: "validation_error";
  field: string;
  message: string;
}

export function validateQueryRequest(body: unknown):
  | { success: true; data: QueryRequest }
  | { success: false; errors: ValidationError[] } {
  const result = QueryRequestSchema.safeParse(body);
  if (result.success) {
    return { success: true, data: result.data };
  }
  return {
    success: false,
    errors: result.error.issues.map((issue) => ({
      error: "validation_error" as const,
      field: issue.path.join(".") || "question",
      message: issue.message,
    })),
  };
}
```

---

## 3. Revisão crítica do código gerado pelo Copilot (Tarefa 3)

### Problema 1 — `.min(1)` não rejeita strings só-espaço

**Código que o Copilot gerou:**
```typescript
question: z.string().min(1).max(500)
```

**Por que é um problema real:**  
`z.string().min(1)` valida comprimento de caracteres — `"   "` (3 espaços) tem length 3, passa na validação. Um atendente que submete acidentalmente um campo vazio (ou um cliente malicioso que envia `"   "`) chega ao pipeline de RAG com uma "pergunta" que gera embedding, consome tokens e retorna resposta vazia ou alucinada.

**Evidência:**
```typescript
z.string().min(1).safeParse("   ")
// → { success: true, data: "   " }  ❌ deveria rejeitar

z.string().trim().min(1).safeParse("   ")
// → { success: false, error: ... }  ✅
```

**Correção aplicada:**
```typescript
question: z.string().trim().min(1, "Question cannot be empty").max(500, "...")
```

---

### Problema 2 — Função retorna tipo opaco sem shape estruturado

**Código que o Copilot gerou:**
```typescript
export function validateQueryRequest(body: unknown) {
  return QueryRequestSchema.safeParse(body);  // retorna SafeParseReturnType<QueryRequest>
}
```

**Por que é um problema real:**  
O tipo de retorno é `z.SafeParseReturnType<QueryRequest>` — específico do Zod. O `handler.ts` que consome essa função ficaria acoplado ao formato interno do Zod (`result.error.issues[].path`, `.message`, `.code`). Se o projeto trocar ou atualizar Zod, todos os consumers quebram. Além disso, o shape do erro não é consistente com o `AppError` que T-007 define para o resto do pipeline.

**Impacto:** cliente do endpoint receberia respostas de erro em dois formatos diferentes dependendo de onde o erro ocorreu (validação vs. pipeline).

**Correção aplicada:**  
Mapear para `ValidationError` com shape controlado pelo projeto: `{ error: "validation_error", field: string, message: string }`. O tipo de retorno é explicitamente `{ success: true; data } | { success: false; errors: ValidationError[] }`.

---

### Problema 3 — Bônus: API do Azure Functions v3 em vez de v4

Esse problema apareceria quando o Copilot implementasse T-006 (`handler.ts`). O stub atual já tem a assinatura errada:

```typescript
// Stub atual (padrão v3 implícito):
export async function queryHandler(/* request */) { ... }

// Copilot geraria (padrão v3 explícito):
import { AzureFunction, Context, HttpRequest } from "@azure/functions";
export const queryHandler: AzureFunction = async (context: Context, req: HttpRequest) => {
  context.res = { status: 200, body: "..." };  // ❌ v3
};

// Correto (padrão v4):
import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";
export async function queryHandler(req: HttpRequest, context: InvocationContext): Promise<HttpResponseInit> {
  return { status: 200, body: "..." };  // ✅ v4
}
app.http("query", { route: "query", methods: ["POST"], handler: queryHandler });
```

A diferença é arquitetural: v4 usa retorno explícito e registro via `app.http()`, não mais `context.res`.

---

## 4. Arquivos criados / modificados

| Arquivo | Ação | Descrição |
|---|---|---|
| `specs/query-endpoint/plan.md` | Preenchido | Conteúdo do plan fornecido pelo exercício |
| `specs/query-endpoint/tasks.md` | Criado | 12 tasks atômicas com critérios verificáveis |
| `src/shared/types.ts` | Implementado | Tipos de domínio: QueryRequest, QueryResponse, Chunk, SearchResult |
| `src/functions/query/validator.ts` | Implementado | Schema Zod com correções da revisão crítica aplicadas |
