"""
ingest.py — Bloco 1: Ingestão de documentos no pipeline RAG da NovaTech.

Estratégia de chunking (justificada por tipo de documento):
- POL-001 (normativo): por subseção ### (3.1, 3.2, 3.3, 3.4+3.5).
  Cada subseção é uma regra independente; cortar entre 3.1 e 3.2 misturaria
  a regra geral de devolução com as exceções de carga perigosa.
- PROC-042 v1/v2 (procedimento): fórmula, tabela de multiplicadores, prazo
  de entrega, condições e regras de transição em chunks separados.
  A tabela de multiplicadores é preservada como unidade atômica para que o
  LLM não receba apenas parte das regiões.
- SLA-2024 (contratual): seção de tiers, tabela de SLAs, definição de
  incidente crítico e penalidades em chunks separados.
- FAQ (informal): cada ### Item como chunk individual.
  Itens selecionados do Anexo B: 3, 8, 15, 32, 38.

Metadados por chunk:
- document_id, version, is_current_version, doc_type, section, source_file
  is_current_version=False para PROC-042 v1 (crítico para resolver conflito).
"""

import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
DOCS_DIR = SCRIPT_DIR.parent / "assets" / "anexos" / "anexo-a-documentos-individuais"
CHROMA_DIR = SCRIPT_DIR / "chroma_db"
COLLECTION_NAME = "novatech_docs"
MODEL_NAME = "all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Utilitário de split por heading markdown
# ---------------------------------------------------------------------------

def _split_sections(text: str, level: str = "##") -> list[tuple[str, str]]:
    """
    Divide um texto markdown em seções pelo nível de heading informado.
    Retorna lista de (heading, conteúdo) mantendo a ordem original.
    """
    escaped = re.escape(level)
    pattern = rf"(?m)^{escaped} (.+?)$"
    matches = list(re.finditer(pattern, text))
    result = []
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        result.append((heading, content))
    return result


# ---------------------------------------------------------------------------
# Chunkers específicos por documento
# ---------------------------------------------------------------------------

def chunk_pol001(text: str) -> list[dict]:
    """
    POL-001 — Política de Devolução.
    Chunks: A (prazo geral), B (exceções / carga perigosa),
            C (procedimento), D (devoluções parciais + custos).
    """
    base_meta = {
        "document_id": "POL-001",
        "version": "3.1",
        "is_current_version": True,
        "doc_type": "normative",
        "source_file": "POL-001-politica-devolucao.md",
    }

    # Localiza a seção "## 3. Regras de Devolução"
    top = dict(_split_sections(text, "##"))
    regras_key = next((k for k in top if k.startswith("3.")), None)
    if not regras_key:
        return []

    sub = _split_sections(top[regras_key], "###")

    chunks = []
    d_parts = []

    for heading, content in sub:
        if "3.1" in heading:
            chunks.append({"chunk_id": "POL-001-A", "text": content,
                           "metadata": {**base_meta, "section": "3.1"}})
        elif "3.2" in heading:
            chunks.append({"chunk_id": "POL-001-B", "text": content,
                           "metadata": {**base_meta, "section": "3.2"}})
        elif "3.3" in heading:
            chunks.append({"chunk_id": "POL-001-C", "text": content,
                           "metadata": {**base_meta, "section": "3.3"}})
        elif "3.4" in heading or "3.5" in heading:
            d_parts.append(content)

    if d_parts:
        chunks.append({"chunk_id": "POL-001-D", "text": "\n\n".join(d_parts),
                       "metadata": {**base_meta, "section": "3.4-3.5"}})

    return chunks


def chunk_proc042(text: str, version: str) -> list[dict]:
    """
    PROC-042 v1 ou v2 — Frete Especial.
    v1 chunks: A (fórmula + fatores de peso), B (multiplicadores regionais), C (prazo + condições).
    v2 chunks: A, B, C (prazo), D (condições + descontos), E (regras de transição).
    is_current_version=True apenas para v2.
    """
    is_v2 = version == "2.0"
    prefix = "PROC-042v2" if is_v2 else "PROC-042"
    src = "PROC-042-v2-frete-especial-revisado.md" if is_v2 else "PROC-042-frete-especial-v1.md"

    base_meta = {
        "document_id": "PROC-042",
        "version": version,
        "is_current_version": is_v2,
        "doc_type": "procedural",
        "source_file": src,
    }

    top = _split_sections(text, "##")
    chunks = []
    c_parts = []  # para v1: seções 3+4 viram um único chunk C

    for heading, content in top:
        if heading.startswith("1."):
            continue  # objetivo não vira chunk — sem valor de retrieval

        elif heading.startswith("2."):
            # Separa fórmula (antes de ### 2.1) da tabela de multiplicadores (### 2.1)
            sub_match = re.search(r"(?m)^### ", content)
            formula_text = content[: sub_match.start()].strip() if sub_match else content

            chunks.append({"chunk_id": f"{prefix}-A", "text": formula_text,
                           "metadata": {**base_meta, "section": "2-formula"}})

            for sub_h, sub_content in _split_sections(content, "###"):
                if "2.1" in sub_h:
                    chunks.append({"chunk_id": f"{prefix}-B", "text": sub_content,
                                   "metadata": {**base_meta, "section": "2.1-multiplicadores"}})

        elif heading.startswith("3."):
            if is_v2:
                chunks.append({"chunk_id": f"{prefix}-C", "text": content,
                               "metadata": {**base_meta, "section": "3-prazo"}})
            else:
                c_parts.append(content)

        elif heading.startswith("4."):
            if is_v2:
                chunks.append({"chunk_id": f"{prefix}-D", "text": content,
                               "metadata": {**base_meta, "section": "4-condicoes"}})
            else:
                c_parts.append(content)

        elif heading.startswith("5.") and is_v2:
            chunks.append({"chunk_id": f"{prefix}-E", "text": content,
                           "metadata": {**base_meta, "section": "5-transicao"}})

    # v1: prazo + condições em chunk único C
    if c_parts:
        chunks.append({"chunk_id": f"{prefix}-C", "text": "\n\n".join(c_parts),
                       "metadata": {**base_meta, "section": "3-4-prazo-condicoes"}})

    return chunks


def chunk_sla2024(text: str) -> list[dict]:
    """
    SLA-2024 — Tabela de SLA por Tipo de Cliente.
    Chunks: A (tiers — sem Platinum!), B (tabela de SLAs gerais e críticos),
            D (definição de incidente crítico), E (penalidades + medição).
    Nota: Anexo B define SLA-2024-B (geral) e SLA-2024-C (crítico) como
    chunks separados, mas no documento fonte estão na mesma tabela da seção 2.
    Mantemos seção 2 como chunk B único; isso é documentado como limitação
    de chunking na análise de resultados.
    """
    base_meta = {
        "document_id": "SLA-2024",
        "version": "2024.1",
        "is_current_version": True,
        "doc_type": "contractual",
        "source_file": "SLA-2024-tabela-sla-clientes.md",
    }

    top = _split_sections(text, "##")
    chunks = []
    e_parts = []

    for heading, content in top:
        if heading.startswith("1."):
            chunks.append({"chunk_id": "SLA-2024-A", "text": content,
                           "metadata": {**base_meta, "section": "1-tiers"}})
        elif heading.startswith("2."):
            # Seção 2 contém SLAs gerais + críticos na mesma tabela
            chunks.append({"chunk_id": "SLA-2024-B", "text": content,
                           "metadata": {**base_meta, "section": "2-tabela-sla"}})
        elif heading.startswith("3."):
            chunks.append({"chunk_id": "SLA-2024-D", "text": content,
                           "metadata": {**base_meta, "section": "3-incidente-critico"}})
        elif heading.startswith("4.") or heading.startswith("5."):
            e_parts.append(content)

    if e_parts:
        chunks.append({"chunk_id": "SLA-2024-E", "text": "\n\n".join(e_parts),
                       "metadata": {**base_meta, "section": "4-5-penalidades-medicao"}})

    return chunks


def chunk_faq(text: str) -> list[dict]:
    """
    FAQ-Atendimento — documento informal.
    Chunka cada ### Item individualmente.
    Mantém apenas os itens relevantes ao Anexo B: 3, 8, 15, 32, 38.
    """
    base_meta = {
        "document_id": "FAQ",
        "version": "não controlada",
        "is_current_version": True,
        "doc_type": "faq",
        "source_file": "FAQ-atendimento.md",
        "is_informal": True,
    }

    relevant = {"3", "8", "15", "32", "38"}
    pattern = r"(?m)^### (Item \d+) — "
    matches = list(re.finditer(pattern, text))

    chunks = []
    for i, m in enumerate(matches):
        item_num = re.search(r"\d+", m.group(1)).group()
        if item_num not in relevant:
            continue
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        chunk_id = f"FAQ-{item_num.zfill(2)}"
        chunks.append({"chunk_id": chunk_id, "text": content,
                       "metadata": {**base_meta, "section": f"Item {item_num}"}})

    return chunks


# ---------------------------------------------------------------------------
# Router: escolhe o chunker correto pelo nome do arquivo
# ---------------------------------------------------------------------------

def chunk_document(filepath: Path) -> list[dict]:
    text = filepath.read_text(encoding="utf-8")
    name = filepath.name

    if name.startswith("POL-001"):
        return chunk_pol001(text)
    elif name == "PROC-042-frete-especial-v1.md":
        return chunk_proc042(text, version="1.0")
    elif name == "PROC-042-v2-frete-especial-revisado.md":
        return chunk_proc042(text, version="2.0")
    elif name.startswith("SLA-2024"):
        return chunk_sla2024(text)
    elif name.startswith("FAQ"):
        return chunk_faq(text)
    else:
        raise ValueError(f"Chunker não definido para: {name}")


# ---------------------------------------------------------------------------
# Ingestão principal
# ---------------------------------------------------------------------------

def ingest():
    print(f"Modelo de embeddings: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    # Coleta todos os chunks de todos os documentos
    all_chunks: list[dict] = []
    for filepath in sorted(DOCS_DIR.glob("*.md")):
        doc_chunks = chunk_document(filepath)
        print(f"  {filepath.name}: {len(doc_chunks)} chunks")
        all_chunks.extend(doc_chunks)

    print(f"\nTotal de chunks: {len(all_chunks)}")

    # Gera embeddings em batch
    texts = [c["text"] for c in all_chunks]
    print("Gerando embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_list=True)

    # Persiste no ChromaDB
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Recria a coleção para garantir estado limpo a cada ingestão
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [c["chunk_id"] for c in all_chunks]
    metadatas = [c["metadata"] for c in all_chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    print(f"\nChromaDB persistido em: {CHROMA_DIR}")
    print(f"Coleção '{COLLECTION_NAME}': {collection.count()} documentos\n")

    # Sumário por documento
    from collections import defaultdict
    by_doc: dict[str, list[str]] = defaultdict(list)
    for c in all_chunks:
        by_doc[c["metadata"]["document_id"]].append(c["chunk_id"])

    print("Chunks por documento:")
    for doc_id, ids_list in sorted(by_doc.items()):
        print(f"  {doc_id}: {ids_list}")


if __name__ == "__main__":
    ingest()
