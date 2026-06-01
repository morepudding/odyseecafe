#!/usr/bin/env python3
"""
scrape_proces_jeanne.py — Scrape le Procès de Jeanne d'Arc depuis Wikisource FR.

Sources scrapées :
  1. Le Procès de Jeanne d'Arc — Robert Brasillach (éd. Gallimard, 1941)
     → procès_brasillach_fr.txt
     → 5 parties : Avertissement, séances publiques, interrogatoires secrets,
       jugement, cause de rechute

  2. Vie de Jeanne d'Arc — Anatole France (Calmann-Lévy, 1908) — preface uniquement
     → vie_anatole_france_preface_fr.txt
     (les chapitres du tome 1 ne sont pas encore transcrits sur Wikisource)

Usage : python src/scrape_proces_jeanne.py
"""
import urllib.request
import json
import re
import time
import random
from pathlib import Path

DEST = Path(__file__).parent.parent / "corpus" / "jeanne"
DEST.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 HistoryCafe-RAG/1.0 (educational, non-commercial)"}
BASE_API = "https://fr.wikisource.org/w/api.php"

# ── 1. Le Procès de Jeanne d'Arc (Brasillach, 1941) ─────────────────────────
# Vérifié sur https://fr.wikisource.org/wiki/Le_Proc%C3%A8s_de_Jeanne_d%E2%80%99Arc
PROCES_OUTPUT = DEST / "proces_brasillach_fr.txt"
PROCES_PAGES = [
    "Le Procès de Jeanne d\u2019Arc/Avertissement",
    "Le Procès de Jeanne d\u2019Arc/Première partie",     # Les séances publiques
    "Le Procès de Jeanne d\u2019Arc/Deuxième partie",     # Les interrogatoires secrets
    "Le Procès de Jeanne d\u2019Arc/Troisième partie",    # Le jugement
    "Le Procès de Jeanne d\u2019Arc/Quatrième partie",    # La cause de rechute
]

# ── 2. Vie de Jeanne d'Arc — Anatole France FR (préface seule, chapitres non transcrits)
ANATOLE_OUTPUT = DEST / "vie_anatole_france_preface_fr.txt"
ANATOLE_PAGES = [
    "Vie de Jeanne d'Arc/tome_1/preface",
]

# ── 3. Jeanne d'Arc — Gabriel Hanotaux (Revue des Deux Mondes, 1910) ─────────
# Vérifié sur https://fr.wikisource.org/wiki/Jeanne_d%E2%80%99Arc_(Hanotaux)
HANOTAUX_OUTPUT = DEST / "hanotaux_jeanne_arc_fr.txt"
HANOTAUX_PAGES = [
    "Jeanne d\u2019Arc (Hanotaux)/01",
    "Jeanne d\u2019Arc (Hanotaux)/02",
    "Jeanne d\u2019Arc (Hanotaux)/03",
    "Jeanne d\u2019Arc (Hanotaux)/04",
    "Jeanne d\u2019Arc (Hanotaux)/05",
    "Jeanne d\u2019Arc (Hanotaux)/06",
    "Jeanne d\u2019Arc (Hanotaux)/07",
    "Jeanne d\u2019Arc (Hanotaux)/08",
]

# ── 4. Articles Wikisource FR divers ─────────────────────────────────────────
ARTICLES_OUTPUT = DEST / "articles_wikisource_fr.txt"
ARTICLES_PAGES = [
    # Sainte-Beuve — Procès de Jeanne d'Arc (Causeries du lundi)
    "Causeries du lundi/Tome II/Proc\u00e8s de Jeanne d\u2019Arc",
    # Louis de Carné — Jeanne d'Arc et sa mission
    "Jeanne d\u2019Arc et sa mission",
    # Dictionnaire apologétique de la foi catholique — entrée Jeanne d'Arc
    "Dictionnaire apolog\u00e9tique de la foi catholique/Jeanne d\u2019Arc",
    # Poésie et vérité — Jeanne d'Arc dans la littérature
    "Jeanne d\u2019Arc dans la litt\u00e9rature - Po\u00e9sie et v\u00e9rit\u00e9",
    # Le Culte de Jeanne d'Arc (article historique)
    "Le Culte de Jeanne d\u2019Arc",
]


def fetch_page_text(page_title: str) -> str | None:
    """Récupère le texte rendu d'une page Wikisource et le nettoie. Retourne None si page introuvable."""
    url = (
        BASE_API
        + "?action=parse"
        + "&page=" + urllib.request.quote(page_title)
        + "&prop=text&format=json&disablelimitreport=1"
    )
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 8 * (attempt + 1) + random.uniform(1, 3)
                print(f" [429 retry {attempt+1}, wait {wait:.0f}s]", end="", flush=True)
                time.sleep(wait)
            elif e.code == 404:
                return None
            else:
                print(f" [HTTP {e.code}]", end="")
                return None
        except Exception as e:
            print(f" [ERR: {e}]", end="")
            return None
    else:
        return None

    if "parse" not in data:
        return None  # page introuvable

    html = data["parse"]["text"]["*"]

    # Nettoyer le HTML
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div[^>]*class="[^"]*headertemplate[^"]*"[^>]*>.*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div[^>]*class="[^"]*ws-noexport[^"]*"[^>]*>.*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div[^>]*class="[^"]*navigation[^"]*"[^>]*>.*?</div>', '', html, flags=re.DOTALL)

    # Convertir balises de structure en texte
    html = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n\n\1\n', html, flags=re.DOTALL)
    html = re.sub(r'<p[^>]*>', '\n', html)
    html = re.sub(r'<br\s*/?>', '\n', html)
    html = re.sub(r'<li[^>]*>', '\n- ', html)

    # Supprimer les balises HTML restantes
    html = re.sub(r'<[^>]+>', '', html)

    # Décoder les entités HTML
    html = html.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ').replace('&#160;', ' ').replace('&quot;', '"').replace('&#39;', "'")

    # Nettoyer les espaces excessifs
    html = re.sub(r'\n{3,}', '\n\n', html)
    html = re.sub(r'[ \t]+', ' ', html)
    return html.strip()


def try_fallback_pages(client_fetch=fetch_page_text) -> str:
    return ""


def scrape_series(pages: list[str], output: Path, title: str) -> bool:
    """Scrape une liste de pages Wikisource vers un fichier de sortie."""
    if output.exists() and output.stat().st_size > 10_000:
        print(f"  ⏭  {output.name} — déjà présent ({output.stat().st_size // 1024} KB), skip")
        return True

    print(f"\n── {title} ──")
    print(f"   → {output}")
    collected = []
    found = 0

    for i, page in enumerate(pages):
        label = page[:70] + "…" if len(page) > 70 else page
        print(f"  [{i+1:02d}/{len(pages)}] {label}", end=" ", flush=True)
        text = fetch_page_text(page)
        if text and len(text) > 100:
            collected.append(f"\n\n{'='*60}\n{page}\n{'='*60}\n\n{text}")
            found += 1
            print(f"✅ {len(text):,} chars")
        else:
            print("⏭ introuvable")
        time.sleep(0.8 + random.uniform(0, 0.4))

    if found == 0:
        print(f"  ❌ Aucune page trouvée pour {title}")
        return False

    full_text = (
        f"{title.upper()}\n"
        f"Source : https://fr.wikisource.org\n"
        + "=" * 60 + "\n"
    ) + "".join(collected)
    output.write_text(full_text, encoding="utf-8")
    size_kb = output.stat().st_size // 1024
    print(f"\n  ✅ {output.name} — {found}/{len(pages)} pages — {size_kb} KB")
    return True


def main():
    print(f"\n=== Scrape Wikisource FR — corpus Jeanne d'Arc ===\n")

    ok1 = scrape_series(
        PROCES_PAGES,
        PROCES_OUTPUT,
        "Le Procès de Jeanne d'Arc — Robert Brasillach (Gallimard, 1941)",
    )
    ok2 = scrape_series(
        ANATOLE_PAGES,
        ANATOLE_OUTPUT,
        "Vie de Jeanne d'Arc — Anatole France (Calmann-Lévy, 1908) — Préface",
    )
    ok3 = scrape_series(
        HANOTAUX_PAGES,
        HANOTAUX_OUTPUT,
        "Jeanne d'Arc — Gabriel Hanotaux (Revue des Deux Mondes, 1910)",
    )
    ok4 = scrape_series(
        ARTICLES_PAGES,
        ARTICLES_OUTPUT,
        "Articles Wikisource FR — Sainte-Beuve, De Carné, Dictionnaire apologétique…",
    )

    outputs = [
        (PROCES_OUTPUT, ok1),
        (ANATOLE_OUTPUT, ok2),
        (HANOTAUX_OUTPUT, ok3),
        (ARTICLES_OUTPUT, ok4),
    ]

    print(f"\n── Résumé ──")
    for path, ok in outputs:
        size = f"  ({path.stat().st_size // 1024} KB)" if path.exists() else ""
        print(f"  {'✅' if ok else '❌'} {path.name}{size}")

    total_mb = sum(
        p.stat().st_size for p, _ in outputs if p.exists()
    ) / (1024 * 1024)
    print(f"\n  Total ajouté : {total_mb:.2f} MB")


if __name__ == "__main__":
    main()
