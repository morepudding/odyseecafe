"""
Tiny editorial database for OdyséeCafé.

Stores validated product/editorial choices separately from the RAG corpus.
"""

from __future__ import annotations

import sqlite3
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = (
    Path("/tmp") / "odyseecafe.sqlite"
    if os.getenv("VERCEL")
    else ROOT_DIR / "data" / "odyseecafe.sqlite"
)


NAPOLEON_THEMES = [
    {
        "slug": "guerre-puissance",
        "name": "Guerre & puissance",
        "description": "Drones, Ukraine, armée française, service, industrie militaire.",
        "sort_order": 1,
    },
    {
        "slug": "autorite-ordre",
        "name": "Autorité & ordre",
        "description": "Justice, police, État faible, violences, sanctions non appliquées.",
        "sort_order": 2,
    },
    {
        "slug": "education-jeunesse",
        "name": "Éducation & jeunesse",
        "description": "SNU, école, discipline, mérite, transmission, génération molle ou sacrifiée.",
        "sort_order": 3,
    },
    {
        "slug": "nation-frontieres",
        "name": "Nation & frontières",
        "description": "Immigration, identité, assimilation, souveraineté, sentiment national.",
        "sort_order": 4,
    },
    {
        "slug": "elites-gouvernement",
        "name": "Élites & gouvernement",
        "description": "Macron, technocrates, Parlement, chefs sans vision, mérite contre caste.",
        "sort_order": 5,
    },
    {
        "slug": "europe-monde",
        "name": "Europe & monde",
        "description": "UE, souveraineté européenne, Russie/USA/Chine, diplomatie, dépendance stratégique.",
        "sort_order": 6,
    },
]


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_editorial_db() -> None:
    with _connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS editorial_themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id TEXT NOT NULL,
                slug TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                UNIQUE(character_id, slug)
            )
            """
        )
        con.executemany(
            """
            INSERT INTO editorial_themes (
                character_id, slug, name, description, sort_order, active
            )
            VALUES ('napoleon', :slug, :name, :description, :sort_order, 1)
            ON CONFLICT(character_id, slug) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                sort_order = excluded.sort_order,
                active = excluded.active
            """,
            NAPOLEON_THEMES,
        )


def list_editorial_themes(character_id: str = "napoleon") -> list[dict]:
    init_editorial_db()
    with _connect() as con:
        rows = con.execute(
            """
            SELECT slug, name, description
            FROM editorial_themes
            WHERE character_id = ? AND active = 1
            ORDER BY sort_order ASC
            """,
            (character_id,),
        ).fetchall()
    return [dict(row) for row in rows]
