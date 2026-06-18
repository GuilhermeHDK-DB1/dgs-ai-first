# Exercício 2.3 — Definição de estratégia de skills do projeto

**Papel:** Desenvolvedor Sênior  
**Ferramentas utilizadas:** GitHub Copilot (SKILL.md Foundation) + Claude (árvore + mapeamento)  
**Repositório:** `D:/novatech-assistant`

---

## 1. Árvore de skills — Foundation → Domain → Artifact (Tarefa 1)

A árvore respeita a hierarquia do repositório (`skills/foundation/`, `skills/domain/`, `skills/artifact/`) e foi derivada diretamente dos artefatos produzidos repetidamente no projeto: endpoints RAG, testes de integração, componentes React, docs técnicos e specs SDD.

```
skills/
├── foundation/                        ← Convenções globais — base para todos os outros
│   ├── typescript-conventions.md      ← SKILL MAIS IMPORTANTE (implementado neste exercício)
│   ├── error-handling.md
│   └── project-structure.md
│
├── domain/                            ← Padrões por camada tecnológica
│   ├── azure-functions-endpoint.md
│   ├── azure-ai-search-integration.md
│   ├── react-components.md
│   └── testing-patterns.md
│
└── artifact/                          ← Receitas de geração específicas
    ├── create-rag-endpoint.md
    ├── create-integration-test.md
    └── create-react-card.md
```

**Por que essa árvore é coerente com o projeto:**  
Cada skill corresponde a um tipo de artefato que será produzido repetidamente. Não há skill que ninguém usaria: `create-rag-endpoint` é usado para cada um dos endpoints RAG; `create-react-card` cobre os cards do painel web; `testing-patterns` governa os testes de integração de cada endpoint. Nenhum skill foi adicionado por simetria — todos têm artefatos concretos como referência.

---

## 2. Mapeamento: criação e consumo por papel (Tarefa 2)

| Arquivo | Nome | Frase de ativação | Quem **cria** | Quem **consome** | Frequência |
|---|---|---|---|---|---|
| `foundation/typescript-conventions` | TypeScript Conventions | "gere/implemente [qualquer artefato TS]" | **Tech Lead** | Dev, TL / Copilot, Claude Code | **Muito alta** — toda geração de código |
| `foundation/error-handling` | Error Handling Patterns | "trate erros em...", "adicione retry em..." | **Tech Lead** | Dev / Copilot | **Alta** — toda função que chama Azure |
| `foundation/project-structure` | Project Structure | "onde fica...", "crie [módulo] no projeto" | **Tech Lead** | Dev, QA / Copilot, Claude | **Alta** — onboarding + toda geração |
| `domain/azure-functions-endpoint` | Azure Functions Endpoint | "crie um endpoint", "implemente Azure Function" | **Dev Sênior** | Dev / Copilot | **Alta** — múltiplos endpoints no projeto |
| `domain/azure-ai-search-integration` | Azure AI Search Integration | "integre com Search", "busque chunks" | **Dev Sênior** | Dev / Copilot | **Média** — 2-3 integrações |
| `domain/react-components` | React Components | "crie componente", "adicione card/formulário" | **Dev Pleno** | Dev Pleno / Copilot | **Média** — painel web |
| `domain/testing-patterns` | Testing Patterns | "escreva teste para...", "adicione coverage" | **QA + Dev Sênior** | Dev, QA / Copilot | **Alta** — todo PR |
| `artifact/create-rag-endpoint` | Create RAG Endpoint | "crie endpoint RAG", "novo endpoint query-like" | **Dev Sênior** | Dev / Copilot | **Média** — 3-4 RAG endpoints total |
| `artifact/create-integration-test` | Create Integration Test | "escreva teste de integração para [endpoint]" | **QA** | Dev, QA / Copilot | **Alta** — 1 por endpoint |
| `artifact/create-react-card` | Create React Card | "crie card de resposta", "novo card de feedback" | **Dev Pleno** | Dev Pleno / Copilot | **Baixa** — ~5 cards total |

**Observação sobre visão de time:**  
A atribuição de criação não é exclusiva de devs. `testing-patterns` e `create-integration-test` são criados pelo QA (que conhece as estratégias de teste do projeto). Tech Lead é responsável pelos 3 skills de Foundation (governa convenções globais). Dev Pleno cria os skills de React, que ele domina melhor do que o Dev Sênior focado em backend.

---

## 3. SKILL.md Foundation implementado com Copilot (Tarefa 3)

**Skill escolhido: `typescript-conventions.md`**

**Por que é o mais importante:**  
Governa toda geração de código TypeScript do projeto. Todo skill de Domain e Artifact depende dele porque todos geram arquivos `.ts`. Sem este skill:
- Skills de artifact geram `any`, `console.log`, exports default
- Skills de domain geram validação Zod sem `.trim()`
- O linter bloqueia o código antes do primeiro commit

**Evidência baseada em dados reais** (exercício 2.2, revisão crítica):  
O Copilot gerou `z.string().min(1)` sem `.trim()` (Problema 1) e retornou `SafeParseReturnType` direto sem mapear para shape estruturado (Problema 2). Esses são exatamente os anti-padrões R-06 e R-08 documentados no SKILL.md.

### Estrutura do SKILL.md gerado

O arquivo `skills/foundation/typescript-conventions.md` contém:

1. **Contexto** — quando o skill é ativado, stack TypeScript do projeto, strict mode
2. **8 regras prescritivas** (R-01 a R-08) com racional direto:
   - R-01: Strict mode inegociável
   - R-02: Zero `any` — use `unknown` + type guard
   - R-03: Zero `console.*` — use logger pino
   - R-04: Named exports only
   - R-05: `z.infer<typeof Schema>` — não duplicar interface
   - R-06: `.trim()` antes de `.min(1)` em strings de usuário
   - R-07: `const` por default, sem `var`
   - R-08: Tipo de retorno explícito em funções públicas exportadas
3. **5 pares DO/DON'T** com código real do projeto:
   - Validação Zod (`validator.ts` do exercício 2.2)
   - Retorno estruturado de erro (`ValidationError` vs `SafeParseReturnType`)
   - Tipos de domínio (`Chunk` com `vigencia` vs `Chunk` com `metadata: any`)
   - Logging (`logger.info(...)` vs `console.log(...)`)
   - Exports (`export function` vs `export default`)
4. **6 anti-padrões tabelados** com código Copilot, motivo do problema e regra correspondente

### Trecho representativo — anti-padrões do SKILL.md

| Anti-padrão | Código que o Copilot gera | Por que é problema | Regra |
|---|---|---|---|
| Sem `.trim()` em Zod | `z.string().min(1)` | Aceita `"   "` como pergunta válida | R-06 |
| Retorno `SafeParseReturnType` | `return schema.safeParse(body)` | Acopla handler ao Zod internals | R-08 |
| `export default function` | `export default function handler()` | Convenção Next.js; quebra tree-shaking | R-04 |
| `console.log` | `console.log("Processing:", data)` | Dados de usuário em stdout; bloqueado pelo lint | R-03 |
| `any` em Azure SDK | `const result: any = await client.search(...)` | Perde tipagem; erros só em runtime | R-02 |
| Interface duplicando schema | `interface X {}` + `z.object({})` | Saem de sincronia ao evoluir o schema | R-05 |

---

## 4. Arquivos criados / modificados

| Arquivo | Ação | Descrição |
|---|---|---|
| `skills/foundation/typescript-conventions.md` | Criado | SKILL.md Foundation com contexto, 8 regras, 5 pares DO/DON'T e 6 anti-padrões |
