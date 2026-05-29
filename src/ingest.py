"""
ingest.py — Chunking + Embedding + Stockage ChromaDB
Embedding : nvidia/llama-nemotron-embed-vl-1b-v2:free via OpenRouter
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import chromadb
import httpx

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

OPENROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
EMBED_MODEL        = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
CORPUS_DIR         = Path(__file__).parent.parent / "corpus"
CHROMA_DIR         = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME    = "napoleon"
CHUNK_SIZE         = 1000   # caractères
CHUNK_OVERLAP      = 150
EMBED_BATCH        = 32     # nb de chunks par appel API

_http = httpx.Client(verify=False, timeout=60)

chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection    = chroma_client.get_or_create_collection(COLLECTION_NAME)


# ── Helpers ──────────────────────────────────────────────────────────────────

def strip_gutenberg(text: str) -> str:
    """Retire les headers/footers Project Gutenberg."""
    start_marker = "*** START OF THE PROJECT GUTENBERG"
    end_marker   = "*** END OF THE PROJECT GUTENBERG"
    if start_marker in text:
        text = text.split(start_marker, 1)[1]
        text = text.split("***", 1)[-1]
    if end_marker in text:
        text = text.split(end_marker, 1)[0]
    return text.strip()


def chunk_text(text: str) -> list[str]:
    """Découpe le texte en chunks avec overlap."""
    chunks, start = [], 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if len(c) > 80]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Appelle l'API OpenRouter directement via httpx."""
    r = _http.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                 "Content-Type": "application/json"},
        json={"model": EMBED_MODEL, "input": texts},
    )
    r.raise_for_status()
    data = r.json().get("data", [])
    return [item["embedding"] for item in data]


# ── Ingestion ────────────────────────────────────────────────────────────────

def ingest_file(filepath: Path, existing_ids: set):
    stem = filepath.stem

    # Skip si déjà ingéré
    if f"{stem}_chunk_0" in existing_ids:
        print(f"  ⏭  {filepath.name} — déjà ingéré, skip")
        return

    text   = filepath.read_text(encoding="utf-8", errors="ignore")
    text   = strip_gutenberg(text)
    chunks = chunk_text(text)
    print(f"  📄 {filepath.name} — {len(chunks)} chunks")

    for i in range(0, len(chunks), EMBED_BATCH):
        batch      = chunks[i : i + EMBED_BATCH]
        embeddings = embed_batch(batch)
        ids        = [f"{stem}_chunk_{i + j}" for j in range(len(batch))]

        collection.add(
            ids        = ids,
            embeddings = embeddings,
            documents  = batch,
            metadatas  = [{"source": filepath.name} for _ in batch],
        )
        nb_batch = (len(chunks) + EMBED_BATCH - 1) // EMBED_BATCH
        print(f"     batch {i // EMBED_BATCH + 1}/{nb_batch} — {len(batch)} chunks ajoutés")


def main():
    txt_files = sorted(CORPUS_DIR.glob("*.txt"))
    if not txt_files:
        print("Aucun fichier .txt trouvé dans corpus/")
        return

    print(f"\n=== Ingestion — {len(txt_files)} fichier(s) ===")
    existing_ids = set(collection.get(include=[])["ids"])

    for f in txt_files:
        ingest_file(f, existing_ids)

    print(f"\n✅ Collection « {COLLECTION_NAME} » : {collection.count()} chunks au total")


if __name__ == "__main__":
    main()
