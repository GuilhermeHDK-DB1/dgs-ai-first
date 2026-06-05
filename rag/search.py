"""
search.py — Bloco 2: Busca semântica no vector store ChromaDB.

Recebe uma pergunta em linguagem natural, gera o embedding com o mesmo modelo
usado na ingestão (all-MiniLM-L6-v2) e retorna os N chunks mais similares
com score de distância cosseno.

Distância cosseno ChromaDB: 0.0 = idêntico, 2.0 = oposto.
Score de similaridade = 1 - distância (para facilitar leitura: 1.0 = perfeito).
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

SCRIPT_DIR = Path(__file__).parent
CHROMA_DIR = SCRIPT_DIR / "chroma_db"
COLLECTION_NAME = "novatech_docs"
MODEL_NAME = "all-MiniLM-L6-v2"

# Cache do modelo e da coleção para reutilização em chamadas múltiplas
_model: SentenceTransformer | None = None
_collection = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def search(query: str, n_results: int = 5) -> list[dict]:
    """
    Busca os chunks mais relevantes para a query.

    Retorna lista de dicts com:
      - chunk_id: ID do chunk (ex: "POL-001-B")
      - text: conteúdo do chunk
      - similarity: float 0-1 (1 = máxima similaridade)
      - distance: distância cosseno original do ChromaDB
      - metadata: metadados (document_id, version, is_current_version, etc.)
    """
    model = _get_model()
    collection = _get_collection()

    query_embedding = model.encode([query], convert_to_list=True)

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        chunks.append({
            "chunk_id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "similarity": round(1 - distance, 4),
            "distance": round(distance, 4),
            "metadata": results["metadatas"][0][i],
        })

    return chunks


def print_results(query: str, results: list[dict]) -> None:
    """Exibe resultados de busca em formato legível."""
    print(f"\nQuery: {query!r}")
    print("-" * 80)
    for r in results:
        version_flag = ""
        if r["metadata"].get("document_id") == "PROC-042":
            v = r["metadata"].get("version", "?")
            current = r["metadata"].get("is_current_version", False)
            version_flag = f" [v{v}{'✓' if current else ' OBSOLETA'}]"
        informal_flag = " [INFORMAL]" if r["metadata"].get("is_informal") else ""
        print(
            f"  [{r['chunk_id']}]{version_flag}{informal_flag} "
            f"sim={r['similarity']:.4f} | "
            f"{r['text'][:120].replace(chr(10), ' ')}..."
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Uso: python search.py "sua pergunta aqui"
        query = " ".join(sys.argv[1:])
        results = search(query, n_results=5)
        print_results(query, results)
    else:
        # Sem argumento: roda 3 queries de exemplo
        test_queries = [
            "Qual o prazo de devolução?",
            "Posso devolver carga perigosa?",
            "Qual o SLA do cliente Gold?",
        ]
        for q in test_queries:
            results = search(q, n_results=5)
            print_results(q, results)
