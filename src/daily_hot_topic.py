"""
daily_hot_topic.py - Select a hot French news controversy for OdyseeCafe.

It writes data/current_topic.json and, when the local web app is running,
pushes the same topic to /api/topic so the textarea is filled immediately.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
CURRENT_TOPIC_PATH = DATA_DIR / "current_topic.json"

RSS_QUERIES = [
    "France polémique actualité politique société",
    "France controverse gouvernement justice école",
    "France débat immigration sécurité laïcité",
    "France prestations sociales allocations impôts polémique",
    "France OQTF immigration délinquance controverse",
    "France réforme colère polémique",
]

RSS_FEEDS = [
    ("Google News France", "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"),
    ("Le Monde une", "https://www.lemonde.fr/rss/une.xml"),
    ("Franceinfo titres", "https://www.francetvinfo.fr/titres.rss"),
]

TOPIC_SCORE_RULES = [
    (
        "conflit_public",
        20,
        ("polemique", "controverse", "colere", "scandale", "accuse", "violence", "emeute"),
    ),
    (
        "autorite_etat",
        18,
        ("gouvernement", "justice", "police", "securite", "etat", "loi", "sanction", "ordre"),
    ),
    (
        "nation_frontieres",
        18,
        ("immigration", "migrant", "etranger", "oqtf", "frontiere", "assimilation", "laicite", "islam"),
    ),
    (
        "argent_social",
        16,
        ("prestation", "allocation", "aides sociales", "rsa", "caf", "impots", "budget", "fraude"),
    ),
    (
        "elite_personnalisee",
        12,
        ("macron", "bayrou", "le pen", "melenchon", "bardella", "retailleau", "borne", "attal"),
    ),
    (
        "vie_quotidienne",
        10,
        ("ecole", "retraites", "agriculteurs", "greve", "logement", "sante", "energie"),
    ),
]


def _fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()


def score_topic(title: str, position: int = 0) -> tuple[int, list[str]]:
    """Score a topic on a bounded, inspectable 0-100 buzz scale."""
    folded = _fold_text(title)
    score = 0
    reasons: list[str] = []

    for label, weight, terms in TOPIC_SCORE_RULES:
        matched = [term for term in terms if term in folded]
        if matched:
            score += weight
            reasons.append(f"{label}:{','.join(matched[:3])}")

    if "?" in title:
        score += 6
        reasons.append("question_directe")

    recency_bonus = max(0, 10 - position)
    if recency_bonus:
        score += recency_bonus
        reasons.append(f"recence:{recency_bonus}")

    return min(score, 100), reasons


def _strip_source(title: str) -> str:
    return re.sub(r"\s+-\s+[^-]{2,80}$", "", title).strip()


def _google_news_rss_url(query: str) -> str:
    params = urllib.parse.urlencode({"q": query, "hl": "fr", "gl": "FR", "ceid": "FR:fr"})
    return f"https://news.google.com/rss/search?{params}"


def fetch_candidates() -> list[dict]:
    candidates: list[dict] = []
    seen: set[str] = set()
    for source_name, url in RSS_FEEDS:
        try:
            for candidate in _fetch_rss_items(url, source_name, limit=20):
                key = candidate["title"].lower()
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(candidate)
        except Exception as exc:
            print(f"[daily_hot_topic] Flux ignore ({source_name}): {exc}", file=sys.stderr)

    for query in RSS_QUERIES:
        try:
            query_candidates = _fetch_rss_items(_google_news_rss_url(query), query, limit=10)
        except Exception as exc:
            print(f"[daily_hot_topic] Recherche ignoree ({query}): {exc}", file=sys.stderr)
            continue
        for candidate in query_candidates:
            key = candidate["title"].lower()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)
    return sorted(candidates, key=lambda item: item["score"], reverse=True)


def _fetch_rss_items(url: str, query: str, limit: int) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "OdyseeCafe/1.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        root = ET.fromstring(response.read())

    items = []
    for position, item in enumerate(root.findall(".//item")[:limit]):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        clean = _strip_source(title)
        if not clean:
            continue
        score, score_reason = score_topic(clean, position=position)
        items.append(
            {
                "title": clean,
                "raw_title": title,
                "url": link,
                "published": published,
                "query": query,
                "score": score,
                "score_reason": score_reason,
            }
        )
    return items


def score_title(title: str) -> int:
    return score_topic(title)[0]


def make_question(title: str) -> str:
    topic = title.strip(" .")
    if topic.endswith("?"):
        return topic
    topic = re.sub(r"^(france\s*:\s*)", "", topic, flags=re.IGNORECASE)
    return f"La France a-t-elle raison de s'embraser sur ce sujet : {topic} ?"


def save_topic(question: str, sources: list[dict]) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "question": question,
        "origin": "daily_hot_topic",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources[:5],
    }
    CURRENT_TOPIC_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def push_to_webapp(payload: dict) -> bool:
    base_url = os.getenv("ODYSSEE_CAFE_URL", "http://127.0.0.1:5005").rstrip("/")
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/api/topic",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def run(push: bool = True, forced_question: str | None = None, forced_source: str | None = None) -> dict:
    if forced_question:
        score, score_reason = score_topic(forced_question)
        sources = [
            {
                "title": "Sujet fourni par la veille OpenClaw",
                "url": forced_source or "",
                "score": score,
                "score_reason": score_reason,
            }
        ]
        payload = save_topic(forced_question, sources)
        payload["origin"] = "openclaw_news_watch"
        payload["pushed_to_webapp"] = push_to_webapp(payload) if push else False
        CURRENT_TOPIC_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    candidates = fetch_candidates()
    if not candidates:
        raise RuntimeError("Aucun sujet d'actualité trouvé.")

    selected = candidates[0]
    question = make_question(selected["title"])
    payload = save_topic(question, candidates[:5])
    payload["pushed_to_webapp"] = push_to_webapp(payload) if push else False
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Injecte le sujet polémique France du jour dans OdyseeCafe.")
    parser.add_argument("--no-push", action="store_true", help="Ecrit seulement data/current_topic.json.")
    parser.add_argument("--question", default=None, help="Force une question choisie par la veille externe.")
    parser.add_argument("--source", default=None, help="URL source principale du sujet force.")
    args = parser.parse_args()
    payload = run(push=not args.no_push, forced_question=args.question, forced_source=args.source)
    print(json.dumps(payload, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[daily_hot_topic] {exc}", file=sys.stderr)
        raise
