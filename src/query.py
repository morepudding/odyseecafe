"""
query.py - RAG retrieval for OdyséeCafé.

Production uses Supabase pgvector. Local development can still fall back to a
populated Chroma collection or a corpus-backed lexical search for quick tests.
"""

from __future__ import annotations

import math
import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from config import env_value, load_local_env, openrouter_api_key

load_local_env(Path(__file__).parent.parent / ".env.local")

ROOT = Path(__file__).parent.parent
CHROMA_DIR = ROOT / "chroma_db"
CORPUS_DIR = ROOT / "corpus"

OPENROUTER_API_KEY = openrouter_api_key()
EMBED_MODEL = env_value(
    "OPENROUTER_EMBED_MODEL",
    "nvidia/llama-nemotron-embed-vl-1b-v2:free",
)
SUPABASE_URL = (
    env_value("SUPABASE_URL") or env_value("NEXT_PUBLIC_SUPABASE_URL")
).rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = (
    env_value("SUPABASE_SERVICE_ROLE_KEY")
    or env_value("SUPABASE_SERVICE_KEY")
)
SUPABASE_RUNTIME_KEY = (
    SUPABASE_SERVICE_ROLE_KEY
    or env_value("SUPABASE_PUBLISHABLE_KEY")
    or env_value("SUPABASE_ANON_KEY")
    or env_value("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")
    or env_value("NEXT_PUBLIC_SUPABASE_ANON_KEY")
)
RAG_BACKEND = env_value("RAG_BACKEND", "supabase" if os.getenv("VERCEL") else "auto").lower()

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 180


STOPWORDS = {
    "alors", "avec", "avoir", "bien", "cette", "dans", "des", "donc",
    "elle", "elles", "est", "etaient", "etre", "fait", "faire", "faut",
    "ils", "les", "leur", "leurs", "mais", "mes", "mon", "nous", "pas",
    "plus", "pour", "que", "qui", "quoi", "sans", "ses", "son", "sur",
    "tes", "toi", "ton", "tous", "tout", "tres", "une", "vous", "your",
    "the", "and", "for", "that", "this", "with", "from", "were", "was",
}


def _http_client(timeout: float = 60):
    import httpx

    return httpx.Client(timeout=timeout, verify=bool(os.getenv("VERCEL")))


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower()


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]{3,}", _normalize(text))
        if token not in STOPWORDS
    ]


def _strip_gutenberg(text: str) -> str:
    start_marker = "*** START OF THE PROJECT GUTENBERG"
    end_marker = "*** END OF THE PROJECT GUTENBERG"
    if start_marker in text:
        text = text.split(start_marker, 1)[1]
        text = text.split("***", 1)[-1]
    if end_marker in text:
        text = text.split(end_marker, 1)[0]
    return text.strip()


def _chunk_text(text: str) -> list[str]:
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


def _corpus_files(character: str) -> list[Path]:
    character_dir = CORPUS_DIR / character
    if character_dir.exists():
        return sorted(character_dir.glob("*.txt"))
    return sorted(CORPUS_DIR.glob("*.txt"))


@lru_cache(maxsize=8)
def _load_corpus_chunks(character: str) -> tuple[dict, ...]:
    chunks = []
    for path in _corpus_files(character):
        try:
            text = _strip_gutenberg(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
        for index, chunk in enumerate(_chunk_text(text)):
            chunk_tokens = _tokens(chunk)
            chunks.append(
                {
                    "text": chunk,
                    "source": path.name,
                    "chunk_index": index,
                    "tokens": tuple(chunk_tokens),
                    "token_set": frozenset(chunk_tokens),
                    "norm": _normalize(chunk),
                }
            )
    return tuple(chunks)


def _embed_text(text: str) -> list[float]:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY/OPEN_ROUTER_API_KEY manquant pour le RAG.")

    with _http_client() as client:
        response = client.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": EMBED_MODEL, "input": [text]},
        )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def _supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_RUNTIME_KEY)


def _supabase_headers(extra: dict | None = None) -> dict:
    headers = {
        "apikey": SUPABASE_RUNTIME_KEY,
        "Authorization": f"Bearer {SUPABASE_RUNTIME_KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers


def _require_supabase() -> None:
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL manquant: le RAG Supabase n'est pas configure.")
    if not SUPABASE_RUNTIME_KEY:
        raise RuntimeError("Cle Supabase manquante: le RAG Supabase n'est pas configure.")


def _raise_supabase_status(response, action: str) -> None:
    try:
        response.raise_for_status()
    except Exception as exc:
        if getattr(response, "status_code", None) == 404:
            raise RuntimeError(
                "Migration Supabase RAG non appliquee: table rag_chunks ou RPC "
                f"match_rag_chunks introuvable pendant {action}."
            ) from exc
        raise


def _supabase_retrieve(question: str, n_results: int, collection_name: str) -> list[dict]:
    _require_supabase()
    embedding = _embed_text(question)

    with _http_client() as client:
        response = client.post(
            f"{SUPABASE_URL}/rest/v1/rpc/match_rag_chunks",
            headers=_supabase_headers(),
            json={
                "query_embedding": embedding,
                "match_character": collection_name,
                "match_count": n_results,
            },
        )
    _raise_supabase_status(response, "la recherche")

    chunks = []
    for row in response.json():
        similarity = float(row.get("similarity") or 0)
        chunks.append(
            {
                "text": row["text"],
                "source": row["source"],
                "distance": round(1 - similarity, 6),
                "similarity": similarity,
            }
        )
    return chunks


def _supabase_count(collection_name: str) -> int:
    _require_supabase()
    with _http_client() as client:
        response = client.get(
            f"{SUPABASE_URL}/rest/v1/rag_chunks",
            params={"select": "id", "character_id": f"eq.{collection_name}"},
            headers=_supabase_headers({"Prefer": "count=exact", "Range": "0-0"}),
        )
    _raise_supabase_status(response, "le comptage")
    content_range = response.headers.get("content-range", "")
    if "/" in content_range:
        try:
            return int(content_range.rsplit("/", 1)[1])
        except ValueError:
            return 0
    return len(response.json())


@lru_cache(maxsize=8)
def _chroma_collection(collection_name: str):
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        return client.get_or_create_collection(collection_name)
    except Exception:
        return None


def _chroma_available(collection_name: str) -> bool:
    collection = _chroma_collection(collection_name)
    if collection is None:
        return False
    try:
        return collection.count() > 0
    except Exception:
        return False


def _chroma_retrieve(question: str, n_results: int, collection_name: str) -> list[dict]:
    collection = _chroma_collection(collection_name)
    if collection is None:
        return []

    embedding = _embed_text(question)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    return [
        {"text": doc, "source": meta["source"], "distance": dist}
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


def _lexical_score(query_tokens: list[str], chunk: dict) -> float:
    if not query_tokens:
        return 0.0
    token_set = chunk["token_set"]
    tf = chunk["tokens"]
    score = 0.0
    for token in query_tokens:
        if token in token_set:
            score += 3.0 + math.log(1 + tf.count(token))
        else:
            stem = token[:6]
            if len(stem) >= 4 and stem in chunk["norm"]:
                score += 0.8
    phrase = " ".join(query_tokens[:4])
    if phrase and phrase in chunk["norm"]:
        score += 4.0
    return score


def _lexical_retrieve(question: str, n_results: int, collection_name: str) -> list[dict]:
    query_tokens = _tokens(question)
    chunks = _load_corpus_chunks(collection_name)
    scored = []
    for chunk in chunks:
        score = _lexical_score(query_tokens, chunk)
        if score > 0:
            scored.append((score, chunk))

    if not scored:
        scored = [(0.01, chunk) for chunk in chunks[:n_results]]

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "text": chunk["text"],
            "source": chunk["source"],
            "distance": round(1 / (1 + score), 6),
        }
        for score, chunk in scored[:n_results]
    ]


def active_backend(collection_name: str = "napoleon") -> str:
    collection_name = (collection_name or "napoleon").strip().lower()
    if RAG_BACKEND == "supabase" or os.getenv("VERCEL"):
        return "supabase"
    if RAG_BACKEND == "chroma":
        return "chroma"
    if RAG_BACKEND == "lexical":
        return "lexical"
    if _supabase_configured():
        return "supabase"
    if _chroma_available(collection_name):
        return "chroma"
    return "lexical"


def retrieve(question: str, n_results: int = 5, collection_name: str = "napoleon") -> list[dict]:
    """Return the best available RAG chunks for a character."""
    collection_name = (collection_name or "napoleon").strip().lower()
    backend = active_backend(collection_name)
    if backend == "supabase":
        return _supabase_retrieve(question, n_results, collection_name)
    if backend == "chroma":
        return _chroma_retrieve(question, n_results, collection_name)
    return _lexical_retrieve(question, n_results, collection_name)


def corpus_chunk_count(collection_name: str = "napoleon") -> int:
    collection_name = (collection_name or "napoleon").strip().lower()
    backend = active_backend(collection_name)
    if backend == "supabase":
        return _supabase_count(collection_name)
    if backend == "chroma":
        collection = _chroma_collection(collection_name)
        return collection.count() if collection is not None else 0
    return len(_load_corpus_chunks(collection_name))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--character", "-c", default="napoleon")
    parser.add_argument("question", nargs="*", default=["Que penses-tu du service militaire ?"])
    args = parser.parse_args()
    question = " ".join(args.question)
    chunks = retrieve(question, collection_name=args.character)
    print(f"\nPersonnage : {args.character}")
    print(f"Backend RAG : {active_backend(args.character)}")
    print(f"Question : {question}")
    print(f"Chunks disponibles : {corpus_chunk_count(args.character)}\n")
    for i, c in enumerate(chunks, 1):
        print(f"-- Chunk {i} [{c['source']}] (dist={c['distance']:.4f}) --")
        print(c["text"][:300])
        print()
