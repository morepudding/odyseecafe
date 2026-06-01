"""
download_jeanne_corpus.py — Téléchargement du corpus Jeanne d'Arc

Sources EN + FR (objectif : ~15-20 MB, comparable au corpus Napoléon) :
  - Twain, Mark — Personal Recollections of Joan of Arc (EN)   [Gutenberg #2489]
  - Lowell, Francis C. — Joan of Arc (EN)                      [Gutenberg #16766]
  - Michelet, Jules — Jeanne d'Arc (FR)                        [Gutenberg #3730]
  - Anatole France — The Life of Joan of Arc Vol.1 (EN)        [Gutenberg #22765]
  - Anatole France — The Life of Joan of Arc Vol.2 (EN)        [Gutenberg #22766]
  - Andrew Lang — The Maid of France (EN)                      [Gutenberg #18964]
  - Mrs. Oliphant — Jeanne d'Arc (EN)                          [Gutenberg #7497]
  - Procès de condamnation — Quicherat (FR)                    [Archive.org]
  - Procès en réhabilitation — Fabre (FR)                      [Archive.org]
  - Procès de condamnation — Wikisource FR (fallback)          [Wikisource API]

Usage : python src/download_jeanne_corpus.py
"""

import sys
import time
from pathlib import Path

import httpx

DEST = Path(__file__).parent.parent / "corpus" / "jeanne"
DEST.mkdir(parents=True, exist_ok=True)

SOURCES = [
    # ── Déjà téléchargés — skip automatique si présents ────────────────────
    {
        "filename": "twain_joan_of_arc_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/2489/pg2489.txt",
        "desc": "Mark Twain — Personal Recollections of Joan of Arc (EN) [Gutenberg #2489]",
    },
    {
        "filename": "lowell_joan_of_arc_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/16766/pg16766.txt",
        "desc": "Francis C. Lowell — Joan of Arc (EN) [Gutenberg #16766]",
    },
    {
        "filename": "michelet_jeanne_arc_fr.txt",
        "url": "https://www.gutenberg.org/cache/epub/3730/pg3730.txt",
        "desc": "Jules Michelet — Jeanne d'Arc (FR) [Gutenberg #3730]",
    },
    # ── Nouvelles sources ───────────────────────────────────────────────────
    {
        "filename": "anatole_france_jeanne_vol1_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/22765/pg22765.txt",
        "desc": "Anatole France — The Life of Joan of Arc Vol. 1 (EN) [Gutenberg #22765]",
    },
    {
        "filename": "anatole_france_jeanne_vol2_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/22766/pg22766.txt",
        "desc": "Anatole France — The Life of Joan of Arc Vol. 2 (EN) [Gutenberg #22766]",
    },
    {
        "filename": "lang_maid_of_france_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/18964/pg18964.txt",
        "desc": "Andrew Lang — The Maid of France (EN) [Gutenberg #18964]",
    },
    {
        "filename": "oliphant_jeanne_arc_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/7497/pg7497.txt",
        "desc": "Mrs. Oliphant — Jeanne d'Arc (EN) [Gutenberg #7497]",
    },
    # ── Sources EN supplémentaires ─────────────────────────────────────────
    {
        "filename": "murray_jeanne_arc_trial_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/57389/pg57389.txt",
        "desc": "Jeanne d'Arc, Maid of Orleans — Trial Translation (EN) [Gutenberg #57389]",
    },
    {
        "filename": "gower_joan_of_arc_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/16933/pg16933.txt",
        "desc": "Lord Ronald Gower — Joan of Arc (EN) [Gutenberg #16933]",
    },
    {
        "filename": "dequincey_joan_of_arc_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/6359/pg6359.txt",
        "desc": "Thomas De Quincey — The English Mail-Coach and Joan of Arc (EN) [Gutenberg #6359]",
    },
    {
        "filename": "schiller_maid_of_orleans_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/6792/pg6792.txt",
        "desc": "Friedrich Schiller — The Maid of Orleans: A Tragedy (EN) [Gutenberg #6792]",
    },
    {
        "filename": "shaw_saint_joan_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/76323/pg76323.txt",
        "desc": "Bernard Shaw — Saint Joan (EN) [Gutenberg #76323]",
    },
    # ── Sources FR supplémentaires (Gutenberg) ────────────────────────────
    {
        "filename": "anatole_france_vie_jeanne_vol1_fr.txt",
        "url": "https://www.gutenberg.org/cache/epub/33692/pg33692.txt",
        "desc": "Anatole France — Vie de Jeanne d'Arc, tome 1 (FR) [Gutenberg #33692]",
    },
    {
        "filename": "anatole_france_vie_jeanne_vol2_fr.txt",
        "url": "https://www.gutenberg.org/cache/epub/34012/pg34012.txt",
        "desc": "Anatole France — Vie de Jeanne d'Arc, tome 2 (FR) [Gutenberg #34012]",
    },
    # ── Sources primaires : Procès (Archive.org) ────────────────────────────
    {
        "filename": "proces_condamnation_quicherat_fr.txt",
        "url": "https://archive.org/download/procsdecondamnat00jean/procsdecondamnat00jean_djvu.txt",
        "desc": "Procès de condamnation — Quicherat (FR) [Archive.org]",
        "fallback": "wikisource_proces",
    },
    {
        "filename": "proces_rehabilitation_fabre_fr.txt",
        "url": "https://archive.org/download/lesprcderhabi00fabr/lesprcderhabi00fabr_djvu.txt",
        "desc": "Procès en réhabilitation — Fabre (FR) [Archive.org]",
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; historycafe-corpus-downloader/1.0)"
}

# ── Fallback Wikisource : Procès de condamnation ─────────────────────────────
WIKISOURCE_PROCES_PAGES = [
    "Procès_de_condamnation_de_Jeanne_d%27Arc/Tome_1/Introduction",
    "Procès_de_condamnation_de_Jeanne_d%27Arc/Tome_1/Acte_I",
    "Procès_de_condamnation_de_Jeanne_d%27Arc/Tome_1/Acte_II",
    "Procès_de_condamnation_de_Jeanne_d%27Arc/Tome_1/Acte_III",
    "Procès_de_condamnation_de_Jeanne_d%27Arc/Tome_1/Acte_IV",
    "Procès_de_condamnation_de_Jeanne_d%27Arc/Tome_1/Acte_V",
    "Procès_de_condamnation_de_Jeanne_d%27Arc/Tome_1/Acte_VI",
    "Procès_de_condamnation_de_Jeanne_d%27Arc/Tome_1/Acte_VII",
    "Procès_de_condamnation_de_Jeanne_d%27Arc/Tome_2/Introduction",
    "Procès_de_condamnation_de_Jeanne_d%27Arc/Tome_2/Acte_I",
    "Procès_de_condamnation_de_Jeanne_d%27Arc/Tome_2/Acte_II",
    "Procès_de_condamnation_de_Jeanne_d%27Arc/Tome_2/Acte_III",
]

WIKISOURCE_API = "https://fr.wikisource.org/w/api.php"


def fetch_wikisource_proces(client: httpx.Client) -> str:
    """Récupère le Procès de condamnation depuis Wikisource FR (API parse)."""
    print("     → Tentative Wikisource FR (API)…")
    parts = []
    for page in WIKISOURCE_PAGES_PROCES:
        try:
            r = client.get(
                WIKISOURCE_API,
                params={"action": "parse", "page": page, "prop": "wikitext", "format": "json"},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
            if wikitext:
                # Retirer les balises wiki les plus communes
                import re
                wikitext = re.sub(r"\{\{[^}]*\}\}", "", wikitext)
                wikitext = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", wikitext)
                wikitext = re.sub(r"={2,}([^=]+)={2,}", r"\n\1\n", wikitext)
                parts.append(wikitext.strip())
            time.sleep(0.5)
        except Exception as e:
            print(f"       ⚠️  Page {page} : {e}")
    return "\n\n---\n\n".join(parts)


WIKISOURCE_PAGES_PROCES = WIKISOURCE_PROCES_PAGES


def download(source: dict, client: httpx.Client) -> bool:
    dest = DEST / source["filename"]
    if dest.exists() and dest.stat().st_size > 10_000:
        print(f"  ⏭  {source['filename']} — déjà présent ({dest.stat().st_size // 1024} KB), skip")
        return True
    print(f"  ⬇  {source['desc']}")
    print(f"     URL : {source['url']}")
    try:
        r = client.get(source["url"], headers=HEADERS, follow_redirects=True, timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
        size_kb = len(r.content) // 1024
        print(f"     ✅ {dest.name} — {size_kb} KB")
        return True
    except Exception as e:
        print(f"     ❌ Échec : {e}")
        if dest.exists() and dest.stat().st_size < 1_000:
            dest.unlink()

        # Fallback Wikisource pour le procès
        if source.get("fallback") == "wikisource_proces":
            print("     → Fallback Wikisource…")
            try:
                text = fetch_wikisource_proces(client)
                if len(text) > 5_000:
                    dest.write_text(text, encoding="utf-8")
                    print(f"     ✅ {dest.name} (Wikisource) — {len(text) // 1024} KB")
                    return True
                else:
                    print("     ❌ Wikisource : contenu trop court, pages introuvables")
            except Exception as e2:
                print(f"     ❌ Wikisource fallback : {e2}")

        return False


def main():
    print(f"\n=== Téléchargement corpus Jeanne d'Arc → {DEST} ===\n")
    client = httpx.Client(verify=False, timeout=60)
    results = []
    for i, source in enumerate(SOURCES):
        ok = download(source, client)
        results.append((source["filename"], ok))
        if i < len(SOURCES) - 1:
            time.sleep(1.0)  # politesse envers les serveurs

    print("\n── Résumé ──")
    ok_count = sum(1 for _, ok in results if ok)
    for fname, ok in results:
        dest = DEST / fname
        size = f"  ({dest.stat().st_size // 1024} KB)" if dest.exists() else ""
        print(f"  {'✅' if ok else '❌'} {fname}{size}")

    total_mb = sum((DEST / f).stat().st_size for f, ok in results if ok and (DEST / f).exists()) / (1024 * 1024)
    print(f"\n{ok_count}/{len(SOURCES)} fichiers — {total_mb:.1f} MB au total dans {DEST}")

    if ok_count < len(SOURCES):
        print("\n⚠️  Certains téléchargements ont échoué. Consulte corpus/SOURCES.md pour les URLs alternatives.")


if __name__ == "__main__":
    main()


import sys
import time
from pathlib import Path

import httpx

DEST = Path(__file__).parent.parent / "corpus" / "jeanne"
DEST.mkdir(parents=True, exist_ok=True)

SOURCES = [
    {
        "filename": "twain_joan_of_arc_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/2489/pg2489.txt",
        "desc": "Mark Twain — Personal Recollections of Joan of Arc (EN) [Gutenberg #2489]",
    },
    {
        "filename": "lowell_joan_of_arc_EN.txt",
        "url": "https://www.gutenberg.org/cache/epub/16766/pg16766.txt",
        "desc": "Francis C. Lowell — Joan of Arc (EN) [Gutenberg #16766]",
    },
    {
        "filename": "michelet_jeanne_arc_fr.txt",
        "url": "https://www.gutenberg.org/cache/epub/3730/pg3730.txt",
        "desc": "Jules Michelet — Jeanne d'Arc (FR) [Gutenberg #3730]",
    },
    {
        "filename": "proces_condamnation_quicherat_fr.txt",
        "url": "https://archive.org/download/procsdecondamnat00jean/procsdecondamnat00jean_djvu.txt",
        "desc": "Procès de condamnation de Jeanne d'Arc — Quicherat (FR) [Archive.org]",
    },
    {
        "filename": "proces_rehabilitation_fabre_fr.txt",
        "url": "https://archive.org/download/lesprcderhabi00fabr/lesprcderhabi00fabr_djvu.txt",
        "desc": "Procès en réhabilitation de Jeanne d'Arc — Fabre (FR) [Archive.org]",
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; historycafe-corpus-downloader/1.0)"
}


def download(source: dict, client: httpx.Client) -> bool:
    dest = DEST / source["filename"]
    if dest.exists() and dest.stat().st_size > 10_000:
        print(f"  ⏭  {source['filename']} — déjà présent ({dest.stat().st_size // 1024} KB), skip")
        return True
    print(f"  ⬇  {source['desc']}")
    print(f"     URL : {source['url']}")
    try:
        r = client.get(source["url"], headers=HEADERS, follow_redirects=True, timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
        size_kb = len(r.content) // 1024
        print(f"     ✅ {dest.name} — {size_kb} KB")
        return True
    except Exception as e:
        print(f"     ❌ Échec : {e}")
        if dest.exists() and dest.stat().st_size < 1_000:
            dest.unlink()
        return False


def main():
    print(f"\n=== Téléchargement corpus Jeanne d'Arc → {DEST} ===\n")
    client = httpx.Client(verify=False, timeout=60)
    results = []
    for i, source in enumerate(SOURCES):
        ok = download(source, client)
        results.append((source["filename"], ok))
        if i < len(SOURCES) - 1:
            time.sleep(1.5)  # politesse envers les serveurs

    print("\n── Résumé ──")
    ok_count = sum(1 for _, ok in results if ok)
    for fname, ok in results:
        print(f"  {'✅' if ok else '❌'} {fname}")
    print(f"\n{ok_count}/{len(SOURCES)} fichiers disponibles dans {DEST}")

    if ok_count < len(SOURCES):
        print("\n⚠️  Certains téléchargements ont échoué. Consulte corpus/SOURCES.md pour les URLs alternatives.")
        sys.exit(1)


if __name__ == "__main__":
    main()
