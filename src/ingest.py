"""
Chunk corpus files, embed them with OpenRouter, and store them in Supabase.

Usage:
  python src/ingest.py
  python src/ingest.py --character napoleon
  python src/ingest.py --character jeanne
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import httpx

sys.path.insert(0, str(Path(__file__).parent))
from config import openrouter_api_key
from supabase_rag import chunk_exists, upsert_chunks, vector_literal


ROOT = Path(__file__).parent.parent
load_dotenv(dotenv_path=ROOT / ".env.local")

OPENROUTER_API_KEY = openrouter_api_key()
EMBED_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
EMBED_BATCH = 32

_http = httpx.Client(timeout=60) if os.getenv("VERCEL") else httpx.Client(verify=False, timeout=60)


def strip_gutenberg(text: str) -> str:
    start_marker = "*** START OF THE PROJECT GUTENBERG"
    end_marker = "*** END OF THE PROJECT GUTENBERG"
    if start_marker in text:
        text = text.split(start_marker, 1)[1]
        text = text.split("***", 1)[-1]
    if end_marker in text:
        text = text.split(end_marker, 1)[0]
    return text.strip()


def chunk_text(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [chunk for chunk in chunks if len(chunk) > 80]


def embed_batch(texts: list[str]) -> list[list[float]]:
    response = _http.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"model": EMBED_MODEL, "input": texts},
    )
    response.raise_for_status()
    return [item["embedding"] for item in response.json().get("data", [])]


def ingest_file(filepath: Path, character: str) -> int:
    stem = filepath.stem
    first_id = f"{character}:{stem}_chunk_0"
    if chunk_exists(first_id):
        print(f"  skip {filepath.name} - already ingested")
        return 0

    text = filepath.read_text(encoding="utf-8", errors="ignore")
    chunks = chunk_text(strip_gutenberg(text))
    print(f"  file {filepath.name} - {len(chunks)} chunks")
    added = 0

    for start in range(0, len(chunks), EMBED_BATCH):
        batch = chunks[start : start + EMBED_BATCH]
        embeddings = embed_batch(batch)
        rows = []
        for offset, (chunk, embedding) in enumerate(zip(batch, embeddings)):
            chunk_index = start + offset
            chunk_id = f"{character}:{stem}_chunk_{chunk_index}"
            rows.append(
                {
                    "id": chunk_id,
                    "character": character,
                    "source": filepath.name,
                    "chunk_index": chunk_index,
                    "content": chunk,
                    "metadata": {
                        "source": filepath.name,
                        "character": character,
                        "stem": stem,
                    },
                    "embedding": vector_literal(embedding),
                }
            )
        upsert_chunks(rows)
        added += len(rows)
        total_batches = (len(chunks) + EMBED_BATCH - 1) // EMBED_BATCH
        print(f"     batch {start // EMBED_BATCH + 1}/{total_batches} - {len(rows)} chunks")

    return added


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest character corpus into Supabase/pgvector")
    parser.add_argument("--character", "-c", default="napoleon")
    args = parser.parse_args()
    character = args.character.lower().strip()
    corpus_dir = ROOT / "corpus" / character

    if not corpus_dir.exists():
        print(f"Corpus folder not found: {corpus_dir}")
        return

    txt_files = sorted(corpus_dir.glob("*.txt"))
    if not txt_files:
        print(f"No .txt files found in {corpus_dir}")
        return

    print(f"\n=== Ingestion - character: {character} - {len(txt_files)} file(s) ===")
    total = 0
    for filepath in txt_files:
        total += ingest_file(filepath, character)
    print(f"\nDone - {total} chunk(s) upserted to Supabase")


if __name__ == "__main__":
    main()
