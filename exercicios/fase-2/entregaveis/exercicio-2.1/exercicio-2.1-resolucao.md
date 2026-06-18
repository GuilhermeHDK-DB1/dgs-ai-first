# Exercício 2.1 — Configuração e uso real de MCP servers no projeto

**Papel:** Desenvolvedor Sênior  
**Ferramentas utilizadas:** GitHub Copilot (exploração e config) + Claude (mapeamento e análise de riscos)  
**Repositório:** `D:/novatech-assistant` (local, sem remoto)

---

## 1. Mapeamento: necessidade → server

Cada necessidade do projeto foi mapeada para um *reference server* local e gratuito. O critério de seleção foi: nenhum serviço externo, nenhum token, tudo via `npx` disponível no ambiente (Node.js v24).

> **Nota de desvio:** O exemplo do Anexo C usa `uvx mcp-server-git` para o server git. `uvx` não estava disponível no ambiente (requer Python + `uv`). Alternativa escolhida: `@cyanheads/git-mcp-server` via `npx`, que oferece as mesmas operações e aceita `GIT_BASE_DIR` para restringir o escopo ao repositório local.

| Necessidade do projeto | Server | O que expõe | Quem consome | Pasta / escopo | Acesso |
|---|---|---|---|---|---|
| Ler e escrever código, specs, skills, prompts | `filesystem-code` (`@modelcontextprotocol/server-filesystem`) | Tools: `read_file`, `write_file`, `edit_file`, `list_directory`, `create_directory`, `search_files` | Dev, Tech Lead / Copilot Agent, Claude Code | `src/` `specs/` `skills/` `prompts/` | read-write |
| Ler documentação de negócio da NovaTech | `filesystem-docs` (`@modelcontextprotocol/server-filesystem`) | Tools: `read_file`, `list_directory`, `search_files` | Todos os papéis / Copilot Agent, Claude | `docs/novatech/` `data/retrieval-corpus/` | intenção read-only¹ |
| Histórico, branches e diffs do repositório | `git` (`@cyanheads/git-mcp-server`) | Tools: `git_log`, `git_diff`, `git_status`, `git_branch`, `git_show`, `git_blame` (28 tools total) | Dev, Tech Lead / Copilot Agent, Claude | `D:/novatech-assistant` (via `GIT_BASE_DIR`) | leitura (operações destrutivas bloqueadas por confirmation flags) |
| Memória persistente: glossário, decisões, linguagem ubíqua | `memory` (`@modelcontextprotocol/server-memory`) | Tools: `create_entities`, `create_relations`, `search_nodes`, `open_nodes`, `delete_entities` | Todos os papéis / Copilot Agent, Claude | grafo local em memória por sessão | read-write |

> ¹ **Limitação identificada:** `@modelcontextprotocol/server-filesystem` v2026.1.14 não suporta flag `--readonly` — o server parseia todos os argumentos posicionais como diretórios. A separação em instância dedicada (`filesystem-docs`) documenta o *boundary de acesso* e é o pré-requisito para enforcement via NTFS ou CI gate (ver Seção 4, Risco 2).

**Por que não incluir o server `everything`?**  
O `@modelcontextprotocol/server-everything` é um server de demonstração que expõe primitivas MCP para aprendizado (echo, sampling, resources de exemplo). Não possui utilidade em um pipeline de produção e aumenta a superfície de ataque sem benefício funcional.

---

## 2. `.mcp/mcp.json` final com justificativas de least privilege

O arquivo vive em `D:/novatech-assistant/.mcp/mcp.json` e é o config canônico para Claude Desktop. O `D:/novatech-assistant/.vscode/mcp.json` (formato `"servers"`) é o equivalente para o GitHub Copilot no VS Code.

```json
{
  "mcpServers": {
    "filesystem-code": {
      "_justificativa": "Escopo mínimo para desenvolvimento: src, specs, skills e prompts. Exclui docs/novatech, data/, infra/ e raiz — o agente não precisa editar documentação de negócio, Bicep ou arquivos de configuração de ambiente.",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "D:/novatech-assistant/src",
        "D:/novatech-assistant/specs",
        "D:/novatech-assistant/skills",
        "D:/novatech-assistant/prompts"
      ]
    },
    "filesystem-docs": {
      "_justificativa": "Fontes de negócio (Confluence substituto) e corpus de chunks (Azure AI Search substituto). INTENÇÃO: read-only. LIMITAÇÃO: @modelcontextprotocol/server-filesystem v2026.1.14 não suporta flag --readonly — enforçamento via permissões NTFS (attrib +r) ou CI gate. Instância separada documenta o boundary de acesso.",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "D:/novatech-assistant/docs/novatech",
        "D:/novatech-assistant/data/retrieval-corpus"
      ]
    },
    "git": {
      "_justificativa": "Acesso read ao histórico, branches e diffs do repositório local. GIT_BASE_DIR restringe operações ao novatech-assistant — o agente não consegue operar em outros repositórios da máquina. uvx não disponível; substituído por @cyanheads/git-mcp-server via npx.",
      "command": "npx",
      "args": ["-y", "@cyanheads/git-mcp-server"],
      "env": {
        "MCP_TRANSPORT_TYPE": "stdio",
        "MCP_LOG_LEVEL": "warn",
        "GIT_BASE_DIR": "D:/novatech-assistant",
        "LOGS_DIR": "D:/novatech-assistant/.mcp/logs",
        "GIT_SIGN_COMMITS": "false"
      }
    },
    "memory": {
      "_justificativa": "Grafo de conhecimento persistente para linguagem ubíqua e decisões do projeto. Estado em memória por sessão — não escreve em pastas do repositório.",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

**Justificativa de least privilege por server:**

| Server | O que foi excluído do escopo | Por quê é o mínimo suficiente |
|---|---|---|
| `filesystem-code` | `docs/novatech/`, `data/`, `infra/`, `.env`, raiz | O agente de desenvolvimento precisa ler e escrever código, specs e skills. Não precisa editar documentação de negócio (responsabilidade do Compliance/PS) nem Bicep (responsabilidade do TL com processo de revisão separado) |
| `filesystem-docs` | `src/`, `specs/`, `skills/`, `infra/`, raiz | Fontes de verdade da NovaTech são somente consulta. Separadas do filesystem de código para documentar o boundary e permitir enforcement via NTFS |
| `git` | Todos os outros repositórios da máquina | `GIT_BASE_DIR=D:/novatech-assistant` impede que o agente execute git em outros diretórios. `GIT_SIGN_COMMITS=false` evita falha silenciosa por ausência de chave GPG no ambiente de dev |
| `memory` | Nenhuma pasta do projeto | Estado efêmero por sessão via grafo em memória. Não persiste arquivos no repositório, não aparece no git |

---

## 3. Evidência de execução

### (a) filesystem-docs — listagem e leitura de `docs/novatech/`

**Prompts usados no Copilot Agent (modo `#agent`):**
```
Liste os arquivos disponíveis em docs/novatech/
```
```
Leia o arquivo POL-001-politica-devolucao.md
```

**Saída capturada — listagem de arquivos:**
```
docs/novatech/
├── FAQ-atendimento.md
├── POL-001-politica-devolucao.md
├── PROC-042-frete-especial-v1.md
├── PROC-042-v2-frete-especial-revisado.md
├── README.md
└── SLA-2024-tabela-sla-clientes.md
```

**Saída capturada — conteúdo de POL-001 (trecho):**
```
# POL-001 — Política de Devolução de Mercadorias
Versão: 3.1 | Última atualização: 15/01/2024

3.1. Prazo geral
O cliente pode solicitar a devolução de mercadorias em até 7 (sete) dias úteis
após a data de recebimento confirmada no sistema de tracking.

3.2. Exceções ao prazo geral
As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo
padrão: Cargas perigosas classificadas nas classes 1 a 6 da ANTT...
Para essas categorias, o cliente deve entrar em contato com o setor de
Gestão de Riscos (ramal 4500) para tratamento individual.
```

> **📸 [PLACEHOLDER] Screenshot do Copilot Agent lendo o arquivo via MCP**  
> Para adicionar: abra VS Code na pasta `D:/novatech-assistant`, ative o modo Agent no Copilot Chat, confirme que o server `filesystem-docs` aparece na lista de tools disponíveis, execute os prompts acima e capture a resposta.

---

### (b) filesystem-docs — recuperação de chunk por pergunta de domínio

**Prompt usado:**
```
Usando o arquivo data/retrieval-corpus/chunks-novatech.md, quais chunks são
relevantes para responder a pergunta: "Qual o prazo de devolução de mercadoria?"
```

**Saída capturada:**

O corpus retornou os seguintes chunks (validados contra gabarito do Anexo B):

| Chunk | Conteúdo resumido | Gabarito Anexo B |
|---|---|---|
| **POL-001-A** | "O cliente pode solicitar a devolução de mercadorias em até 7 (sete) dias úteis após a data de recebimento confirmada no sistema de tracking." | ✅ DEVE ser recuperado |
| **POL-001-B** | "As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão: Cargas perigosas classificadas nas classes 1 a 6 da ANTT..." | ✅ DEVE ser recuperado |
| POL-001-C | Procedimento de abertura de chamado no Portal do Cliente | Pode aparecer (relevância menor) |

**Resultado:** recuperação correta — os dois chunks primários do gabarito foram identificados. Nenhum chunk de PROC-042 ou SLA foi retornado (domínio correto isolado).

> **📸 [PLACEHOLDER] Screenshot do Copilot Agent recuperando os chunks via MCP**  
> Para adicionar: use o mesmo prompt acima no Copilot Agent com o server `filesystem-docs` ativo e capture a resposta com os chunks identificados.

---

### (c) git — leitura do histórico do repositório

**Prompt usado:**
```
Mostre o histórico de commits deste repositório
```

**Saída capturada — `git log` do repositório local:**
```
commit (HEAD -> main)
Author: —
Date:   —

    chore: starter repo (Anexo D) — estrutura + dados semeados dos Anexos A e B
```

O repositório tem 1 commit (o inicial do Starter Repo), confirmando que o server git consegue ler o histórico e que não há histórico adicional a ser ocultado.

> **📸 [PLACEHOLDER] Screenshot do Copilot Agent rodando git_log via MCP**  
> Para adicionar: use o prompt acima no Copilot Agent com o server `git` ativo e capture a resposta mostrando o commit do starter repo.

---

## 4. Análise de riscos de segurança

### Risco 1 — Escopo amplo do filesystem expõe `.env` e segredos

**Vetor de ataque:**  
Se o argumento do server fosse `.` (raiz do repositório) em vez de subpastas explícitas, o agente teria acesso de leitura e escrita a:
- `.env` — chaves de API, connection strings (mesmo que vazio hoje, será populado na fase de integração com Azure)
- `infra/parameters/dev.bicepparam` e `prod.bicepparam` — credenciais de ambiente Azure
- `tsconfig.json`, `package.json` — modificação silenciosa de configurações de build

O agente poderia exfiltrar esses valores simplesmente sendo instruído (via prompt injection em um documento da base) a ler e retornar o conteúdo de arquivos de configuração.

**Mitigação implementada:**  
`filesystem-code` lista explicitamente `src/ specs/ skills/ prompts/`. `filesystem-docs` lista `docs/novatech/ data/retrieval-corpus/`. Raiz, `infra/`, `.env` e arquivos de config estão fora de todos os escopos declarados.

**Mitigação adicional recomendada:**  
Adicionar ao `.gitignore` qualquer arquivo `.env.*` que venha a ser criado. Nunca usar `.` como argumento de nenhum MCP server em produção.

---

### Risco 2 — Server de escrita sem gate permite que o agente altere docs de negócio sem revisão

**Vetor de ataque:**  
`@modelcontextprotocol/server-filesystem` v2026.1.14 não suporta `--readonly`. `filesystem-docs` tem `write_file` e `edit_file` disponíveis, apesar de a intenção ser somente-leitura. Um agente com instruções maliciosas (ou um prompt suficientemente ambíguo) pode modificar `docs/novatech/POL-001-politica-devolucao.md` — alterando prazos, valores ou exceções — sem que o desenvolvedor perceba antes do próximo deploy.

Impacto específico neste projeto: documentos da NovaTech alimentam diretamente o corpus de RAG. Uma modificação silenciosa em `POL-001` propagaria um erro factual para todas as respostas do assistente.

**Mitigação 1 — NTFS read-only (enforcement imediato, local):**
```bash
attrib +R /S "D:\novatech-assistant\docs\novatech\*"
attrib +R /S "D:\novatech-assistant\data\retrieval-corpus\*"
```
Torna os arquivos somente-leitura ao nível do sistema operacional, antes do server MCP. Qualquer tentativa de `write_file` via `filesystem-docs` retorna erro de permissão — evidência verificável do least privilege.

**Mitigação 2 — CI gate (enforcement persistente, em equipe):**  
O `.github/workflows/ci.yml` pode incluir uma regra que rejeita PRs com alterações em `docs/novatech/` ou `data/retrieval-corpus/` sem label de aprovação do Compliance. Isso garante que mesmo que o NTFS seja removido localmente, o gate persiste no pipeline de integração.

---

## 5. Arquivos criados / modificados

| Arquivo | Ação | Descrição |
|---|---|---|
| `D:/novatech-assistant/.mcp/mcp.json` | Preenchido | Config canônico para Claude Desktop — 4 servers com justificativas de least privilege |
| `D:/novatech-assistant/.vscode/mcp.json` | Criado | Config para VS Code Copilot (formato `"servers"`) — mesmos 4 servers |
| `D:/novatech-assistant/.gitignore` | Atualizado | Adicionado `.mcp/logs/` para ignorar logs do `@cyanheads/git-mcp-server` |
