"""
Ingest a character corpus into Supabase pgvector.

Prerequisites:
  - Run supabase/migrations/20260613_rag_pgvector.sql on the Supabase project.
  - Set SUPABASE_URL/NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.local.

Usage:
  python src/ingest_supabase.py --character napoleon
  python src/ingest_supabase.py --character napoleon --force
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from config import env_value, load_local_env, openrouter_api_key  # noqa: E402

load_local_env(Path(__file__).parent.parent / ".env.local")

ROOT = Path(__file__).parent.parent
CORPUS_ROOT = ROOT / "corpus"
EMBED_MODEL = env_value(
    "OPENROUTER_EMBED_MODEL",
    "nvidia/llama-nemotron-embed-vl-1b-v2:free",
)
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 180
EMBED_BATCH = 24
UPSERT_BATCH = 96


def required_env(name: str, fallback: str = "") -> str:
    value = env_value(name) or (env_value(fallback) if fallback else "")
    if not value:
        label = f"{name}/{fallback}" if fallback else name
        raise SystemExit(f"Variable d'environnement manquante: {label}")
    return value


OPENROUTER_API_KEY = required_env("OPENROUTER_API_KEY", "OPEN_ROUTER_API_KEY")
SUPABASE_URL = (
    env_value("SUPABASE_URL") or required_env("NEXT_PUBLIC_SUPABASE_URL")
).rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = required_env("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_KEY")


def http_client(timeout: float = 120) -> httpx.Client:
    return httpx.Client(timeout=timeout, verify=bool(os.getenv("VERCEL")))


def supabase_headers(extra: dict | None = None) -> dict:
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers


def raise_supabase_status(response: httpx.Response, action: str) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if response.status_code == 404:
            raise SystemExit(
                "Migration Supabase RAG non appliquee: table rag_chunks introuvable "
                f"pendant {action}."
            ) from exc
        raise


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
    text = re.sub(r"\n{3,}", "\n\n", text)
    chunks = []
    start = 0
    step = CHUNK_SIZE - CHUNK_OVERLAP
    while start < len(text):
        chunk = text[start : start + CHUNK_SIZE].strip()
        if len(chunk) > 120:
            chunks.append(chunk)
        start += step
    return chunks


def corpus_files(character: str) -> list[Path]:
    character_dir = CORPUS_ROOT / character
    if character_dir.exists():
        return sorted(character_dir.glob("*.txt"))
    return sorted(CORPUS_ROOT.glob("*.txt"))


def stable_id(character: str, source: Path, chunk_index: int) -> str:
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", source.stem).strip("-")[:90]
    return f"{character}:{safe_stem}:{chunk_index:05d}"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_records(character: str) -> list[dict]:
    records = []
    files = corpus_files(character)
    if not files:
        raise SystemExit(f"Aucun fichier .txt trouve pour le personnage: {character}")

    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(strip_gutenberg(text))
        print(f"{path.name}: {len(chunks)} chunks")
        for index, chunk in enumerate(chunks):
            records.append(
                {
                    "id": stable_id(character, path, index),
                    "character_id": character,
                    "source": path.name,
                    "chunk_index": index,
                    "text": chunk,
                    "content_hash": content_hash(chunk),
                    "token_count": len(chunk.split()),
                }
            )
    return records


def fetch_existing_hashes(character: str) -> dict[str, str]:
    existing: dict[str, str] = {}
    offset = 0
    page_size = 1000

    with http_client() as client:
        while True:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/rag_chunks",
                params={
                    "select": "id,content_hash",
                    "character_id": f"eq.{character}",
                    "order": "id.asc",
                },
                headers=supabase_headers({"Range": f"{offset}-{offset + page_size - 1}"}),
            )
            raise_supabase_status(response, "la lecture des hashes existants")
            rows = response.json()
            for row in rows:
                existing[row["id"]] = row["content_hash"]
            if len(rows) < page_size:
                break
            offset += page_size

    return existing


def embed_batch(texts: list[str]) -> list[list[float]]:
    with http_client() as client:
        response = client.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": EMBED_MODEL, "input": texts},
        )
    response.raise_for_status()
    return [item["embedding"] for item in response.json()["data"]]


def upsert_records(records: list[dict]) -> None:
    for start in range(0, len(records), UPSERT_BATCH):
        batch = records[start : start + UPSERT_BATCH]
        with http_client() as client:
            response = client.post(
                f"{SUPABASE_URL}/rest/v1/rag_chunks",
                params={"on_conflict": "id"},
                headers=supabase_headers(
                    {"Prefer": "resolution=merge-duplicates,return=minimal"}
                ),
                json=batch,
            )
        raise_supabase_status(response, "l'upsert des chunks")


def ingest(character: str, force: bool = False) -> None:
    records = build_records(character)
    print(f"\nTotal local: {len(records)} chunks")

    existing = {} if force else fetch_existing_hashes(character)
    pending = [
        record
        for record in records
        if force or existing.get(record["id"]) != record["content_hash"]
    ]

    print(f"Deja a jour: {len(records) - len(pending)}")
    print(f"A ingerer: {len(pending)}")
    if not pending:
        return

    for start in range(0, len(pending), EMBED_BATCH):
        batch = pending[start : start + EMBED_BATCH]
        embeddings = embed_batch([record["text"] for record in batch])
        for record, embedding in zip(batch, embeddings):
            record["embedding"] = embedding
        upsert_records(batch)
        print(f"Batch {start // EMBED_BATCH + 1}/{(len(pending) + EMBED_BATCH - 1) // EMBED_BATCH}: {len(batch)} chunks")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest corpus chunks into Supabase pgvector")
    parser.add_argument("--character", "-c", default="napoleon")
    parser.add_argument("--force", action="store_true", help="Re-embed and upsert every chunk")
    args = parser.parse_args()

    character = args.character.lower().strip()
    ingest(character, force=args.force)


if __name__ == "__main__":
    main()
