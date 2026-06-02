from __future__ import annotations

import os
from functools import lru_cache
from typing import Iterable

import httpx

from config import supabase_key, supabase_url


TABLE_NAME = "rag_chunks"
MATCH_FUNCTION = "match_rag_chunks"


def vector_literal(values: Iterable[float]) -> str:
    return "[" + ",".join(f"{float(v):.9g}" for v in values) + "]"


def _headers(prefer: str | None = None) -> dict:
    key = supabase_key()
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY/SUPABASE_KEY is required")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


@lru_cache(maxsize=1)
def _http_client() -> httpx.Client:
    if not supabase_url():
        raise RuntimeError("SUPABASE_URL is required")
    return httpx.Client(
        base_url=f"{supabase_url().rstrip('/')}/rest/v1",
        timeout=60,
        verify=bool(os.getenv("VERCEL")),
    )


def match_chunks(
    query_embedding: list[float],
    character: str = "napoleon",
    match_count: int = 5,
) -> list[dict]:
    response = _http_client().post(
        f"/rpc/{MATCH_FUNCTION}",
        headers=_headers(),
        json={
            "query_embedding": vector_literal(query_embedding),
            "match_count": match_count,
            "character_filter": character,
        },
    )
    response.raise_for_status()

    return [
        {
            "text": row.get("content", ""),
            "source": row.get("source", ""),
            "distance": float(row.get("distance", 0)),
            "metadata": row.get("metadata") or {},
        }
        for row in response.json()
    ]


def upsert_chunks(rows: list[dict]) -> int:
    if not rows:
        return 0
    response = _http_client().post(
        f"/{TABLE_NAME}",
        params={"on_conflict": "id"},
        headers=_headers("resolution=merge-duplicates,return=minimal"),
        json=rows,
    )
    response.raise_for_status()
    return len(rows)


def count_chunks(character: str = "napoleon") -> int:
    response = _http_client().get(
        f"/{TABLE_NAME}",
        params={"select": "id", "character": f"eq.{character}"},
        headers={**_headers(), "Prefer": "count=exact"},
    )
    response.raise_for_status()
    count = response.headers.get("Content-Range", "0").split("/")[-1]
    return int(count) if count.isdigit() else 0


def chunk_exists(chunk_id: str) -> bool:
    response = _http_client().get(
        f"/{TABLE_NAME}",
        params={"select": "id", "id": f"eq.{chunk_id}", "limit": 1},
        headers=_headers(),
    )
    response.raise_for_status()
    return bool(response.json())
