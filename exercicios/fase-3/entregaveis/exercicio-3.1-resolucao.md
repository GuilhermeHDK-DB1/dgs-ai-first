# Exercício 3.1 - Structured output e verificações determinísticas

## 1. Entendimento do problema

O problema central é que a resposta do assistente está em texto livre. Isso permite que respostas sem fonte, com estrutura inconsistente ou até com conteúdo proibido passem pelo sistema.

A proposta deste exercício é separar claramente dois níveis de controle:

- Prompt (probabilístico): orienta o modelo a responder no formato esperado.
- Código (determinístico): valida e bloqueia respostas inválidas de forma garantida.

Objetivo prático do harness:

- Exigir formato estruturado com campos obrigatórios.
- Rejeitar saída inválida antes de qualquer uso.
- Aplicar regras de negócio críticas com bloqueio explícito.
- Em falha, devolver resposta segura padrão.

## 2. Schema Zod de structured output

Exemplo de schema com campos obrigatórios e bloqueio de chaves extras.

    import { z } from 'zod';

    export const assistantResponseSchema = z
      .object({
        answer: z.string().trim().min(1, 'answer é obrigatório'),
        source_document: z.string().trim().min(1, 'source_document é obrigatório'),
        confidence_score: z
          .number({ invalid_type_error: 'confidence_score deve ser número' })
          .min(0, 'confidence_score deve ser >= 0')
          .max(1, 'confidence_score deve ser <= 1'),
      })
      .strict();

    export type AssistantResponse = z.infer<typeof assistantResponseSchema>;

Decisões relevantes:

- .strict() evita aceitação silenciosa de campos extras.
- source_document com trim + min(1) evita string vazia.
- confidence_score limitado ao intervalo de 0 a 1.

## 3. response-validator.ts (harness determinístico)

Implementação exemplo contendo:

- Validação de schema.
- Guardrail 1 (source_document obrigatório).
- Guardrail 2 (carga perigosa + devolução exige negativa).
- Log estruturado de motivo de bloqueio.
- Fallback seguro em qualquer falha.

    import pino from 'pino';
    import { z } from 'zod';

    const logger = pino({ name: 'response-validator' });

    export const assistantResponseSchema = z
      .object({
        answer: z.string().trim().min(1, 'answer é obrigatório'),
        source_document: z.string().trim().min(1, 'source_document é obrigatório'),
        confidence_score: z
          .number({ invalid_type_error: 'confidence_score deve ser número' })
          .min(0)
          .max(1),
      })
      .strict();

    export type AssistantResponse = z.infer<typeof assistantResponseSchema>;

    const SAFE_FALLBACK: AssistantResponse = {
      answer: 'Não consegui confirmar essa informação com segurança. Vou encaminhar para validação humana.',
      source_document: 'fallback-safe-response',
      confidence_score: 0,
    };

    function normalizeText(input: string): string {
      return input
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase();
    }

    function includesAny(text: string, terms: string[]): boolean {
      return terms.some((term) => text.includes(term));
    }

    function violatesDangerousCargoReturnPolicy(answer: string): boolean {
      const normalized = normalizeText(answer);

      const hasDangerousCargo = includesAny(normalized, [
        'carga perigosa',
        'produto perigoso',
        'material perigoso',
      ]);

      const hasReturnContext = includesAny(normalized, [
        'devolucao',
        'devolver',
        'devolvido',
      ]);

      if (!hasDangerousCargo || !hasReturnContext) {
        return false;
      }

      const hasExplicitDenial = includesAny(normalized, [
        'nao e permitido',
        'nao permitido',
        'nao e possivel',
        'nao pode',
        'devolucao nao permitida',
      ]);

      const hasAffirmativeReturn = includesAny(normalized, [
        'e permitido devolver',
        'devolucao permitida',
        'pode devolver',
        'e possivel devolver',
      ]);

      if (hasAffirmativeReturn) {
        return true;
      }

      return !hasExplicitDenial;
    }

    export function validateAssistantResponse(raw: unknown): AssistantResponse {
      const parsed = assistantResponseSchema.safeParse(raw);

      if (!parsed.success) {
        logger.warn(
          {
            event: 'assistant_response_rejected',
            reason: 'schema_validation_failed',
            issues: parsed.error.issues,
          },
          'Resposta bloqueada pelo schema'
        );
        return SAFE_FALLBACK;
      }

      const response = parsed.data;

      if (!response.source_document || response.source_document.trim() === '') {
        logger.warn(
          {
            event: 'assistant_response_rejected',
            reason: 'missing_source_document',
          },
          'Resposta sem source_document'
        );
        return SAFE_FALLBACK;
      }

      if (violatesDangerousCargoReturnPolicy(response.answer)) {
        logger.warn(
          {
            event: 'assistant_response_rejected',
            reason: 'dangerous_cargo_return_policy_violation',
            source_document: response.source_document,
          },
          'Resposta bloqueada por política de carga perigosa e devolução'
        );
        return SAFE_FALLBACK;
      }

      return response;
    }

## 4. Code review rápido (problemas reais encontrados)

Problema 1

- Tipo: bug de validação
- Achado: schema sem .strict() aceitaria campos extras inesperados.
- Impacto: payload fora do contrato pode seguir adiante sem controle.
- Correção aplicada: adição de .strict().

Problema 2

- Tipo: bug de regra de negócio
- Achado: checagem simples por substring de carga perigosa + devolução é frágil.
- Impacto: variações com acento, flexão verbal e frases equivalentes escapam da regra.
- Correção aplicada: normalização de texto (lowercase + remoção de acento) e lista de variantes semânticas.

Problema 3

- Tipo: risco operacional
- Achado: sem log estruturado de motivo de bloqueio.
- Impacto: difícil auditar rejeições e monitorar regressões de guardrail.
- Correção aplicada: eventos com reason padronizado e metadados mínimos.

## 5. Como este entregável atende aos critérios

- Schema válido com Zod e campos obrigatórios: sim.
- Bloqueio real dos 2 guardrails: sim, com retorno de fallback seguro.
- Code review com problemas reais e correções: sim, três pontos objetivos.
- Separação entre prompt probabilístico e código determinístico: explícita e aplicada.

## 6. Resumo executivo

Este harness reduz risco de alucinação operacional ao impedir que respostas malformadas ou incompatíveis com política crítica cheguem ao usuário final. O prompt melhora a chance de acerto; a validação determinística garante governança.
