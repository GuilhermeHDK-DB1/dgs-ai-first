// Tipos de domínio compartilhados — NovaTech Assistant
// Gerado em T-002 (ver specs/query-endpoint/tasks.md)

/** Input do POST /api/query */
export interface QueryRequest {
  question: string;
  conversationId?: string;
}

/**
 * Chunk recuperado pelo Azure AI Search.
 * O campo `vigencia` é obrigatório para ordenação ADR-0003:
 * chunks mais recentes têm prioridade no context budget.
 */
export interface Chunk {
  id: string;
  content: string;
  sourceDocument: string;
  /** ISO date string ou null — usado para priorização (ADR-0003) */
  vigencia?: string;
  score: number;
}

/** Resultado da busca vetorial */
export interface SearchResult {
  chunks: Chunk[];
  totalCount: number;
}

/** Resposta do POST /api/query */
export interface QueryResponse {
  answer: string;
  /** Lista de sourceDocument únicos dos chunks usados no prompt */
  sourceDocuments: string[];
  conversationId?: string;
}
