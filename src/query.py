"""
query.py — Recherche sémantique dans ChromaDB
Embedding de la question via le même modèle qu'à l'ingestion.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import chromadb
import httpx
from config import openrouter_api_key

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

OPENROUTER_API_KEY = openrouter_api_key()
EMBED_MODEL        = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
CHROMA_DIR         = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME    = "napoleon"

_http = httpx.Client(timeout=30) if os.getenv("VERCEL") else httpx.Client(verify=False, timeout=30)

chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection    = chroma_client.get_or_create_collection(COLLECTION_NAME)


def retrieve(question: str, n_results: int = 5) -> list[dict]:
    """Retourne les N chunks les plus proches de la question."""
    r = _http.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                 "Content-Type": "application/json"},
        json={"model": EMBED_MODEL, "input": [question]},
    )
    r.raise_for_status()
    q_embedding = r.json()["data"][0]["embedding"]

    results = collection.query(
        query_embeddings = [q_embedding],
        n_results        = n_results,
        include          = ["documents", "metadatas", "distances"],
    )

    return [
        {"text": doc, "source": meta["source"], "distance": dist}
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) or "Que penses-tu du service militaire ?"
    chunks   = retrieve(question)
    print(f"\nQuestion : {question}\n")
    for i, c in enumerate(chunks, 1):
        print(f"── Chunk {i} [{c['source']}] (dist={c['distance']:.4f}) ──")
        print(c["text"][:300])
        print()
