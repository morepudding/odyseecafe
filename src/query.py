"""
Semantic retrieval for HistoryCafe through Supabase/pgvector.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
import httpx

from config import openrouter_api_key
from supabase_rag import count_chunks, match_chunks


load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

OPENROUTER_API_KEY = openrouter_api_key()
EMBED_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"

_http = httpx.Client(timeout=30) if os.getenv("VERCEL") else httpx.Client(verify=False, timeout=30)


class _CollectionProxy:
    """Compatibility shim for webapp chunk_count."""

    def __init__(self, name: str):
        self.name = name

    def count(self) -> int:
        return count_chunks(self.name)


# Exposed for webapp chunk_count compatibility.
collection = _CollectionProxy("napoleon")


def embed_question(question: str) -> list[float]:
    response = _http.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"model": EMBED_MODEL, "input": [question]},
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def retrieve(question: str, n_results: int = 5, collection_name: str = "napoleon") -> list[dict]:
    """Return the nearest chunks for a question."""
    return match_chunks(
        embed_question(question),
        character=collection_name,
        match_count=n_results,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--character", "-c", default="napoleon")
    parser.add_argument("question", nargs="*", default=["Que penses-tu du service militaire ?"])
    args = parser.parse_args()
    question = " ".join(args.question)
    chunks = retrieve(question, collection_name=args.character)
    print(f"\nPersonnage : {args.character}")
    print(f"Question : {question}\n")
    for i, chunk in enumerate(chunks, 1):
        print(f"-- Chunk {i} [{chunk['source']}] (dist={chunk['distance']:.4f}) --")
        print(chunk["text"][:300])
        print()
