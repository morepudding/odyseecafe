"""
Editorial persistence for OdyseeCafe.

Themes stay in code for now. Daily dossiers are archived in Supabase so Vercel
and local runs share the same history.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from functools import lru_cache

import httpx

from config import supabase_key, supabase_url


EDITORIAL_DOSSIERS_TABLE = "editorial_dossiers"

NAPOLEON_THEMES = [
    {
        "slug": "guerre-puissance",
        "name": "Guerre & puissance",
        "description": "Drones, Ukraine, armee francaise, service, industrie militaire.",
        "sort_order": 1,
    },
    {
        "slug": "autorite-ordre",
        "name": "Autorite & ordre",
        "description": "Justice, police, Etat faible, violences, sanctions non appliquees.",
        "sort_order": 2,
    },
    {
        "slug": "education-jeunesse",
        "name": "Education & jeunesse",
        "description": "SNU, ecole, discipline, merite, transmission, generation molle ou sacrifiee.",
        "sort_order": 3,
    },
    {
        "slug": "nation-frontieres",
        "name": "Nation & frontieres",
        "description": "Immigration, identite, assimilation, souverainete, sentiment national.",
        "sort_order": 4,
    },
    {
        "slug": "argent-prestations",
        "name": "Argent public & prestations",
        "description": "Prestations sociales, aides publiques, impots, fraude, couts, redistribution.",
        "sort_order": 5,
    },
    {
        "slug": "elites-gouvernement",
        "name": "Elites & gouvernement",
        "description": "Macron, technocrates, Parlement, chefs sans vision, merite contre caste.",
        "sort_order": 6,
    },
    {
        "slug": "europe-monde",
        "name": "Europe & monde",
        "description": "UE, souverainete europeenne, Russie/USA/Chine, diplomatie, dependance strategique.",
        "sort_order": 7,
    },
]


def list_editorial_themes(character_id: str = "napoleon") -> list[dict]:
    if character_id != "napoleon":
        return []
    return [
        {
            "slug": theme["slug"],
            "name": theme["name"],
            "description": theme["description"],
        }
        for theme in sorted(NAPOLEON_THEMES, key=lambda item: item["sort_order"])
    ]


def _supabase_headers(prefer: str | None = None) -> dict:
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
def _supabase_http() -> httpx.Client:
    url = supabase_url()
    if not url:
        raise RuntimeError("SUPABASE_URL is required")
    return httpx.Client(
        base_url=f"{url.rstrip('/')}/rest/v1",
        timeout=60,
        verify=bool(os.getenv("VERCEL")),
    )


def _score_from_line(line: str) -> int | None:
    match = re.search(r":\s*(10|[0-9])\s*/\s*(10|5)", line)
    if not match:
        return None
    score = int(match.group(1))
    denominator = int(match.group(2))
    return min(score * 2, 10) if denominator == 5 else score


def dossier_metrics(dossier: str, sources: list[dict] | None = None) -> dict:
    relevance_scores: list[int] = []
    buzz_scores: list[int] = []
    status_counts = {"trouve": 0, "fragile": 0, "non_trouve": 0}
    high_score_count = 0
    justification_count = 0
    item_count = 0

    for raw_line in (dossier or "").splitlines():
        line = raw_line.strip()
        if line.startswith("- ") and not line.startswith("- [S"):
            item_count += 1
        if line.startswith("Pertinence au sujet"):
            score = _score_from_line(line)
            if score is not None:
                relevance_scores.append(score)
                if score > 8:
                    high_score_count += 1
            continue
        if line.startswith("Potentiel buzz"):
            score = _score_from_line(line)
            if score is not None:
                buzz_scores.append(score)
                if score > 8:
                    high_score_count += 1
            continue
        if line.startswith("Justification score"):
            justification_count += 1
            continue
        if line.startswith("Statut"):
            status = line.split(":", 1)[-1].strip().lower().replace(" ", "_")
            status = status.replace("é", "e").replace("è", "e").replace("ê", "e")
            if status in status_counts:
                status_counts[status] += 1

    def avg(values: list[int]) -> float | None:
        return round(sum(values) / len(values), 2) if values else None

    return {
        "item_count": item_count,
        "source_count": len(sources or []),
        "avg_relevance": avg(relevance_scores),
        "avg_buzz": avg(buzz_scores),
        "high_score_count": high_score_count,
        "justification_count": justification_count,
        "high_scores_missing_justification": max(high_score_count - justification_count, 0),
        **status_counts,
    }


def archive_editorial_dossier(
    question: str,
    dossier: str,
    *,
    angle: str = "",
    sources: list[dict] | None = None,
    character_id: str = "napoleon",
    origin: str = "manual",
    day: str | None = None,
) -> dict | None:
    question = (question or "").strip()
    dossier = (dossier or "").strip()
    if not question or not dossier:
        return None

    now = datetime.now().isoformat(timespec="seconds")
    payload = {
        "day": day or now[:10],
        "character_id": character_id,
        "question": question,
        "origin": origin,
        "dossier": dossier,
        "angle": angle or "",
        "sources": sources or [],
        "metrics": dossier_metrics(dossier, sources=sources),
        "updated_at": now,
    }

    try:
        response = _supabase_http().post(
            f"/{EDITORIAL_DOSSIERS_TABLE}",
            params={"on_conflict": "day,character_id,question"},
            headers=_supabase_headers("resolution=merge-duplicates,return=representation"),
            json=payload,
        )
        response.raise_for_status()
    except Exception as exc:
        print(f"[editorial_db] Supabase archive skipped: {exc}")
        return None

    data = response.json()
    return data[0] if isinstance(data, list) and data else None


def list_editorial_dossiers(limit: int = 14, character_id: str | None = None) -> list[dict]:
    params: dict[str, str | int] = {
        "select": "id,day,character_id,question,origin,metrics,created_at,updated_at",
        "order": "day.desc,updated_at.desc",
        "limit": limit,
    }
    if character_id:
        params["character_id"] = f"eq.{character_id}"
    try:
        response = _supabase_http().get(
            f"/{EDITORIAL_DOSSIERS_TABLE}",
            params=params,
            headers=_supabase_headers(),
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"[editorial_db] Supabase dossier list skipped: {exc}")
        return []
