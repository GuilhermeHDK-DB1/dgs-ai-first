"""
prompt_builder.py — Bloco 3: Montagem do prompt completo para o LLM.

Estrutura do prompt (engenharia de contexto):
  [ESTÁTICO]  SYSTEM_PROMPT  (~350 tokens) — identidade, guardrails, regras de fonte
  [DINÂMICO]  Contexto recuperado (~500-2000 tokens) — chunks do pipeline
  [DINÂMICO]  Pergunta do usuário (~20-50 tokens)

Partes estáticas vão em toda query; partes dinâmicas mudam a cada chamada.
O system prompt é passado para o Claude como bloco de instrução inicial.
"""

SYSTEM_PROMPT = """\
Você é o Assistente de Atendimento da NovaTech, uma empresa de logística.
Seu papel é responder dúvidas da equipe de atendimento ao cliente com base
exclusivamente na documentação oficial da NovaTech fornecida no contexto abaixo.

## Regras obrigatórias

1. **Sempre cite a fonte**: ao responder, informe o documento de origem
   (ex: "conforme POL-001, seção 3.2" ou "conforme SLA-2024, seção 2").

2. **Nunca invente informações**: se um prazo, valor ou regra não estiver
   explícito no contexto fornecido, diga que a informação não foi encontrada.
   Não extrapole nem use conhecimento externo.

3. **Quando não encontrar resposta**: diga explicitamente
   "Não encontrei essa informação na documentação disponível"
   e sugira escalar para o supervisor ou consultar o departamento responsável.

4. **Prioridade de fontes** (em caso de conflito):
   - Documentos normativos (POL-xxx) > Documentos de procedimento (PROC-xxx)
     > Documentos contratuais (SLA-xxx) > FAQ (informal, não validado).
   - Para a PROC-042: sempre use a versão mais recente (v2.0, de novembro/2023),
     exceto se o chamado foi aberto antes de 01/12/2023.
   - Informações do FAQ devem ser sinalizadas como "orientação informal" quando
     contrariem ou complementem documentos normativos.

5. **Responda em português formal**, mas acessível para atendentes.

6. **Tiers de cliente válidos**: Gold, Silver e Standard. Não existe tier Platinum.
   Se o cliente mencionar Platinum, corrija gentilmente.

## Formato de resposta

- Resposta objetiva (1-3 parágrafos).
- Ao final, sempre informe: **Fonte:** [documento] — [seção ou item].
- Se mais de uma fonte for relevante, liste todas.
"""

CONTEXT_HEADER = "## Contexto recuperado da documentação NovaTech\n"
QUESTION_HEADER = "## Pergunta do atendente\n"


def build_prompt(query: str, chunks: list[dict]) -> str:
    """
    Monta o prompt completo: system prompt + contexto dinâmico + pergunta.

    Args:
        query: Pergunta em linguagem natural do atendente.
        chunks: Lista de dicts retornados por search.search().

    Returns:
        String completa do prompt pronta para colar no Claude (chat manual).
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk["metadata"]
        version_note = ""
        if meta.get("document_id") == "PROC-042":
            v = meta.get("version", "?")
            current = meta.get("is_current_version", False)
            version_note = f" | Versão {v}" + (" [ATUAL]" if current else " [OBSOLETA]")
        informal_note = " | ⚠ Documento informal, não validado" if meta.get("is_informal") else ""

        header = (
            f"### Chunk {i}: {chunk['chunk_id']}"
            f" | {meta.get('document_id', '')} — {meta.get('section', '')}"
            f"{version_note}{informal_note}"
        )
        context_parts.append(f"{header}\n\n{chunk['text']}")

    context_block = "\n\n---\n\n".join(context_parts) if context_parts else (
        "_Nenhum chunk relevante foi recuperado para esta pergunta._"
    )

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{CONTEXT_HEADER}\n{context_block}\n\n"
        f"{QUESTION_HEADER}\n{query}"
    )
    return prompt


def estimate_tokens(text: str) -> int:
    """Estimativa grosseira: ~0.75 palavras por token (regra prática)."""
    return int(len(text.split()) / 0.75)


def print_prompt_stats(prompt: str) -> None:
    lines = prompt.split("\n")
    tokens = estimate_tokens(prompt)
    print(f"  Linhas: {len(lines)} | Palavras: {len(prompt.split())} | ~{tokens} tokens estimados")


if __name__ == "__main__":
    # Teste de montagem sem ChromaDB
    mock_chunks = [
        {
            "chunk_id": "POL-001-B",
            "text": "### 3.2. Exceções ao prazo geral\n\nCargas perigosas (classes 1-6 ANTT) NÃO são elegíveis para devolução pelo processo padrão.",
            "similarity": 0.92,
            "metadata": {
                "document_id": "POL-001",
                "version": "3.1",
                "is_current_version": True,
                "doc_type": "normative",
                "section": "3.2",
                "is_informal": False,
            },
        }
    ]
    prompt = build_prompt("Posso devolver carga perigosa?", mock_chunks)
    print(prompt[:800], "\n[...truncado...]")
    print_prompt_stats(prompt)
