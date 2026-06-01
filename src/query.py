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

_http = httpx.Client(timeout=30) if os.getenv("VERCEL") else httpx.Client(verify=False, timeout=30)

chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
# Collection "napoleon" exposée au niveau module pour compatibilité webapp (chunk_count)
collection    = chroma_client.get_or_create_collection("napoleon")


def retrieve(question: str, n_results: int = 5, collection_name: str = "napoleon") -> list[dict]:
    """Retourne les N chunks les plus proches de la question."""
    r = _http.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                 "Content-Type": "application/json"},
        json={"model": EMBED_MODEL, "input": [question]},
    )
    r.raise_for_status()
    q_embedding = r.json()["data"][0]["embedding"]

    col = (collection if collection_name == "napoleon"
           else chroma_client.get_or_create_collection(collection_name))

    results = col.query(
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
    import sys, argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--character", "-c", default="napoleon")
    parser.add_argument("question", nargs="*", default=["Que penses-tu du service militaire ?"])
    args = parser.parse_args()
    question = " ".join(args.question)
    chunks   = retrieve(question, collection_name=args.character)
    print(f"\nPersonnage : {args.character}")
    print(f"Question : {question}\n")
    for i, c in enumerate(chunks, 1):
        print(f"── Chunk {i} [{c['source']}] (dist={c['distance']:.4f}) ──")
        print(c["text"][:300])
        print()
