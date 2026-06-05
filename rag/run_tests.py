"""
run_tests.py — Bloco 4: Executa os 6 testes de retrieval e gera relatório.

Para cada pergunta:
  1. Executa busca semântica (search.py)
  2. Monta o prompt completo (prompt_builder.py)
  3. Compara chunks recuperados com gabarito do Anexo B
  4. Salva prompt completo em arquivo para teste manual no Claude

Saída: tabela de resultados no terminal + arquivos prompts/pergunta_N.txt

Gabarito extraído do Anexo B (mapa de cobertura):
  P1 Prazo de devolução        → POL-001-A, POL-001-B
  P2 Devolver carga perigosa?  → POL-001-B (+ FAQ-03)
  P3 SLA cliente Gold          → SLA-2024-B
  P4 SLA cliente Platinum      → SLA-2024-A (confirma que não existe Platinum)
  P5 Frete 600kg Manaus        → PROC-042v2-A, PROC-042v2-B
  P6 Frete 300kg Salvador      → nenhum (carga abaixo de 500kg — não coberta)
"""

import os
from pathlib import Path
from search import search
from prompt_builder import build_prompt, print_prompt_stats

SCRIPT_DIR = Path(__file__).parent
PROMPTS_DIR = SCRIPT_DIR / "prompts_para_claude"

# ---------------------------------------------------------------------------
# Gabarito do Anexo B
# ---------------------------------------------------------------------------

TEST_CASES = [
    {
        "id": "P1",
        "query": "Qual o prazo de devolução?",
        "expected_chunks": ["POL-001-A", "POL-001-B"],
        "propósito": "Baseline — regra geral de devolução",
        "armadilha": None,
    },
    {
        "id": "P2",
        "query": "Posso devolver carga perigosa?",
        "expected_chunks": ["POL-001-B", "FAQ-03"],
        "propósito": "Negação explícita — chunking separa exceção da regra geral",
        "armadilha": "Se POL-001-A aparecer antes de POL-001-B, o LLM pode afirmar que é possível devolver",
    },
    {
        "id": "P3",
        "query": "Qual o SLA do cliente Gold?",
        "expected_chunks": ["SLA-2024-B"],
        "propósito": "Recuperação em domínio contratual / tabela",
        "armadilha": None,
    },
    {
        "id": "P4",
        "query": "Qual o SLA do cliente Platinum?",
        "expected_chunks": ["SLA-2024-A"],
        "propósito": "Teste de alucinação — tier Platinum não existe",
        "armadilha": "Pipeline ou LLM NÃO pode inventar SLA para tier inexistente",
    },
    {
        "id": "P5",
        "query": "Frete para 600kg para Manaus?",
        "expected_chunks": ["PROC-042v2-A", "PROC-042v2-B"],
        "propósito": "Multi-chunk + conflito de versão v1 vs v2",
        "armadilha": "PROC-042-B (v1 OBSOLETA) pode aparecer; multiplicadores Norte: 1.6 (v1) vs 1.8 (v2)",
    },
    {
        "id": "P6",
        "query": "Frete para 300kg para Salvador?",
        "expected_chunks": [],
        "propósito": "Não-cobertura documental — carga abaixo de 500kg",
        "armadilha": "Pipeline não deve retornar chunks relevantes; LLM não pode inventar cálculo",
    },
]

# ---------------------------------------------------------------------------
# Avaliação de match
# ---------------------------------------------------------------------------

def evaluate_match(retrieved_ids: list[str], expected_ids: list[str]) -> tuple[bool, str]:
    """
    Avalia se os chunks esperados estão entre os recuperados.
    Retorna (is_match, detalhes).
    """
    if not expected_ids:
        # Espera-se que nenhum chunk seja fortemente relevante
        # Consideramos sucesso se o top chunk tiver similaridade < 0.6
        return None, "SEM COBERTURA (verificar scores)"

    found = [eid for eid in expected_ids if eid in retrieved_ids]
    missing = [eid for eid in expected_ids if eid not in retrieved_ids]

    if not missing:
        return True, f"✅ Todos encontrados: {found}"
    elif found:
        return False, f"⚠️  Parcial: encontrados={found} | faltando={missing}"
    else:
        return False, f"❌ Nenhum encontrado. Esperados: {expected_ids}"


def check_version_contamination(retrieved: list[dict]) -> str | None:
    """Verifica se chunks PROC-042 v1 (obsoleta) aparecem no resultado."""
    obsolete = [
        r["chunk_id"] for r in retrieved
        if r["metadata"].get("document_id") == "PROC-042"
        and not r["metadata"].get("is_current_version", True)
    ]
    if obsolete:
        return f"⚠️  CONTAMINAÇÃO v1: {obsolete} (multiplicadores obsoletos)"
    return None


# ---------------------------------------------------------------------------
# Runner principal
# ---------------------------------------------------------------------------

def run_tests(n_results: int = 5) -> None:
    os.makedirs(PROMPTS_DIR, exist_ok=True)

    print("=" * 80)
    print("PIPELINE RAG — NOVATECH | Relatório de Testes")
    print("Modelo: all-MiniLM-L6-v2 | Vector store: ChromaDB (cosseno)")
    print("=" * 80)

    # Tabela de resultados
    rows = []

    for tc in TEST_CASES:
        print(f"\n{'─' * 60}")
        print(f"[{tc['id']}] {tc['query']}")
        print(f"     Propósito: {tc['propósito']}")
        if tc["armadilha"]:
            print(f"     ⚠ Armadilha: {tc['armadilha']}")

        retrieved = search(tc["query"], n_results=n_results)

        print(f"\n  Chunks recuperados (top {n_results}):")
        for r in retrieved:
            meta = r["metadata"]
            v_note = ""
            if meta.get("document_id") == "PROC-042":
                current = meta.get("is_current_version", False)
                v_note = f" v{meta.get('version','?')}{'[ATUAL]' if current else '[OBSOLETA]'}"
            informal = " [INFORMAL]" if meta.get("is_informal") else ""
            print(f"    {r['chunk_id']:20s}{v_note}{informal} sim={r['similarity']:.4f}")

        retrieved_ids = [r["chunk_id"] for r in retrieved]
        is_match, match_detail = evaluate_match(retrieved_ids, tc["expected_chunks"])
        version_warn = check_version_contamination(retrieved)

        print(f"\n  Gabarito Anexo B : {tc['expected_chunks'] or '[ nenhum ]'}")
        print(f"  Resultado        : {match_detail}")
        if version_warn:
            print(f"  {version_warn}")

        # Monta e salva o prompt para teste manual no Claude
        prompt = build_prompt(tc["query"], retrieved)
        prompt_path = PROMPTS_DIR / f"{tc['id'].lower()}_prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")
        print(f"\n  Prompt salvo em : {prompt_path.name}")
        print(f"  ", end="")
        print_prompt_stats(prompt)

        rows.append({
            "id": tc["id"],
            "query": tc["query"],
            "retrieved": ", ".join(retrieved_ids[:5]),
            "expected": ", ".join(tc["expected_chunks"]) or "—",
            "match": match_detail,
            "version_warn": version_warn or "",
        })

    # Tabela resumo final
    print("\n\n" + "=" * 80)
    print("TABELA RESUMO DE RESULTADOS")
    print("=" * 80)
    col_q = 36
    col_r = 38
    col_e = 32
    col_m = 45
    header = (
        f"{'ID':<4} {'Pergunta':<{col_q}} {'Chunks Recuperados':<{col_r}} "
        f"{'Esperados (Anexo B)':<{col_e}} {'Resultado'}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['id']:<4} {row['query'][:col_q-1]:<{col_q}} "
            f"{row['retrieved'][:col_r-1]:<{col_r}} "
            f"{row['expected'][:col_e-1]:<{col_e}} "
            f"{row['match']}"
        )
        if row["version_warn"]:
            print(f"{'':4} {row['version_warn']}")

    print("\n" + "=" * 80)
    print(f"Prompts para teste manual no Claude salvos em: {PROMPTS_DIR}")
    print("Copie o conteúdo de cada arquivo e cole no Claude para obter a resposta do LLM.")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
