// T-005 — Validador de input do query endpoint
// Implementado com GitHub Copilot + revisão crítica aplicada (ver exercicio-2.2-resolucao.md)

import { z } from "zod";

// ─── Schema ──────────────────────────────────────────────────────────────────

export const QueryRequestSchema = z.object({
  // REVISÃO CRÍTICA #1 — Copilot gerou: z.string().min(1).max(500)
  // Problema: .min(1) aceita "   " (string só-espaço) como válido.
  // Correção: .trim() antes de .min(1) rejeita strings só-espaço.
  question: z
    .string()
    .trim()
    .min(1, "Question cannot be empty")
    .max(500, "Question cannot exceed 500 characters"),

  conversationId: z.string().uuid().optional(),
});

/** Tipo TypeScript inferido diretamente do schema — evita duplicação */
export type QueryRequest = z.infer<typeof QueryRequestSchema>;

// ─── Tipo de erro estruturado ─────────────────────────────────────────────────

// REVISÃO CRÍTICA #2 — Copilot retornava result.error.issues diretamente (array Zod bruto).
// Problema: cliente teria de tratar formato Zod interno, acoplando à biblioteca.
// Correção: mapear para ValidationError com shape consistente com AppError (T-007).
export interface ValidationError {
  error: "validation_error";
  field: string;
  message: string;
}

// ─── Função de validação ──────────────────────────────────────────────────────

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
