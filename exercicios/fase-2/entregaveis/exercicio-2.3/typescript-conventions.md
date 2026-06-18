# Skill: TypeScript Conventions — NovaTech Assistant

> **Skill Foundation.** Este skill governa toda geração de código TypeScript no projeto.
> Todo skill de Domain e Artifact depende dele. Leia antes de gerar qualquer artefato `.ts`.

---

## Contexto

Este projeto usa TypeScript com **strict mode obrigatório** (`tsconfig.json: "strict": true`).
O backend é Azure Functions v4. O painel web é React. Toda lógica compartilhada vive em `src/shared/`.

Stack de validação: **Zod** para schemas de entrada e saída.  
Stack de logging: **pino** via `src/shared/logger.ts` — `console.*` é proibido em `src/`.  
Padrão de exports: **named exports only** — sem default exports.

Quando este skill é ativado:
- Qualquer prompt que peça geração ou modificação de arquivo `.ts` em `src/`
- Frases como: "implemente", "crie", "refatore", "adicione" + qualquer artefato TypeScript

---

## Regras prescritivas

### R-01 — Strict mode é inegociável

`tsconfig.json` tem `"strict": true`. Nunca adicione `@ts-ignore`, `as any` ou `// @ts-nocheck`
para contornar erros do compilador. Se o compilador reclamar, corrija o tipo.

### R-02 — Zero `any` — use `unknown` com type guard

`any` desliga o compilador. Use `unknown` e estreite o tipo com type guard ou cast explícito
com razão documentada. O linter bloqueia `any` implícito e explícito.

### R-03 — Zero `console.*` — use o logger do projeto

`console.log`, `console.error`, `console.warn` são proibidos em `src/`.
Importe `logger` de `src/shared/logger.ts`. Cada log deve ter `requestId` quando disponível.

### R-04 — Named exports only

Sem `export default`. Named exports permitem tree-shaking correto e refactoring seguro.
`export default` é aceito apenas em `src/web/` (convenção React — componentes de página).

### R-05 — Use `z.infer<typeof Schema>` — nunca duplique interfaces Zod

Se há um schema Zod, derive o tipo TypeScript dele. Definir a interface separadamente
cria divergência silenciosa quando o schema evolui.

### R-06 — `.trim()` antes de `.min(1)` em strings de usuário

Toda string que vem de input externo (HTTP body, query string) deve ter `.trim()` antes
de qualquer validação de comprimento. `"   "` tem length 3 mas é semanticamente vazia.

### R-07 — `const` por default, `let` com mutação explícita, sem `var`

`var` não existe neste projeto. Prefira `const`. Use `let` apenas quando a variável
precisa ser reatribuída — e documente por quê com um comentário se a mutação não for óbvia.

### R-08 — Tipo de retorno explícito em funções públicas exportadas

TypeScript infere, mas funções que fazem parte da API pública de um módulo (exportadas)
devem ter tipo de retorno anotado. Isso estabiliza a interface e revela breaking changes
no momento do build, não em runtime.

---

## Exemplos — DO / DON'T

### Validação com Zod

```typescript
// ✅ DO — schema é a fonte de verdade; tipo inferido; .trim() presente
import { z } from "zod";

export const QueryRequestSchema = z.object({
  question: z
    .string()
    .trim()                                      // R-06
    .min(1, "Question cannot be empty")
    .max(500, "Question cannot exceed 500 characters"),
  conversationId: z.string().uuid().optional(),
});

export type QueryRequest = z.infer<typeof QueryRequestSchema>;  // R-05
```

```typescript
// ❌ DON'T — interface duplicada; sem .trim(); .min(1) aceita "   "
export interface QueryRequest {          // interface duplica o schema — divergência futura
  question: string;
}

export const QueryRequestSchema = z.object({
  question: z.string().min(1).max(500),  // aceita "   " como válido
});
```

---

### Retorno estruturado de erro

```typescript
// ✅ DO — shape próprio do projeto; desacopla do Zod internals; tipo discriminado explícito
export interface ValidationError {
  error: "validation_error";
  field: string;
  message: string;
}

export function validateQueryRequest(body: unknown):
  | { success: true; data: QueryRequest }
  | { success: false; errors: ValidationError[] } {
  const result = QueryRequestSchema.safeParse(body);
  if (result.success) return { success: true, data: result.data };
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

```typescript
// ❌ DON'T — retorna tipo interno do Zod; acopla consumer ao formato da biblioteca
export function validateQueryRequest(body: unknown) {  // R-08: sem tipo de retorno
  return QueryRequestSchema.safeParse(body);           // expõe SafeParseReturnType<T>
}
```

---

### Tipos de domínio

```typescript
// ✅ DO — tipos nomeados, sem any, vigencia explícita para rastreabilidade ADR-0003
export interface Chunk {
  id: string;
  content: string;
  sourceDocument: string;
  vigencia?: string;   // ISO date — priorização de versão mais recente (ADR-0003)
  score: number;
}
```

```typescript
// ❌ DON'T — any destrói type safety em toda a cadeia
export interface Chunk {
  id: string;
  content: string;
  metadata: any;       // R-02: use tipo explícito ou Record<string, unknown>
}
```

---

### Logging

```typescript
// ✅ DO — pino estruturado com contexto de request
import { logger } from "../shared/logger.js";

export async function queryHandler(req: HttpRequest, context: InvocationContext) {
  const requestId = req.headers.get("x-request-id") ?? crypto.randomUUID();
  logger.info({ requestId, question: body.question }, "query received");  // R-03
}
```

```typescript
// ❌ DON'T — console.log proibido em src/; sem requestId; dado sensível exposto
console.log("Processing query:", question);   // R-03
console.log("Azure response:", fullResponse); // dados de usuário em log não estruturado
```

---

### Exports

```typescript
// ✅ DO — named exports; arquivo de serviço
export function buildPrompt(chunks: Chunk[], question: string): string { ... }
export function estimateTokens(text: string): number { ... }
```

```typescript
// ❌ DON'T — default export em módulo de serviço
export default {                // R-04: quebra tree-shaking; renaming arbitrário no import
  buildPrompt,
  estimateTokens,
};
```

---

## Anti-padrões — o que o Copilot gera sem este skill

| Anti-padrão | Código que o Copilot gera | Por que é problema | Regra |
|---|---|---|---|
| Sem `.trim()` em Zod | `z.string().min(1)` | Aceita `"   "` como pergunta válida; embedding vazio consumindo tokens | R-06 |
| Retorno `SafeParseReturnType` | `return schema.safeParse(body)` | Acopla handler ao formato interno do Zod; shape inconsistente com `AppError` | R-08 |
| `export default function` | `export default function handler()` | Convenção Next.js; incompatível com o padrão do projeto; quebra tree-shaking | R-04 |
| `console.log` | `console.log("Processing:", data)` | Dados de usuário em stdout não estruturado; bloqueado pelo linter | R-03 |
| `any` em resultado Azure SDK | `const result: any = await client.search(...)` | Perde tipagem do SDK; erros de acesso a campo só aparecem em runtime | R-02 |
| Interface duplicando Zod schema | `interface X { ... }` + `z.object({ ... })` | Dois tipos saem de sincronia silenciosamente ao evoluir o schema | R-05 |
