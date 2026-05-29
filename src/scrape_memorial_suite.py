#!/usr/bin/env python3
"""
Suite du scraping du Mémorial de Sainte-Hélène.
Reprend depuis les chapitres manquants (Tome 1 Ch10 jusqu'à la fin).
"""
import urllib.request
import json
import re
import time
import random

OUTPUT = r"C:\RomainOpen\historycafe\corpus\las_cases_memorial_wikisource_fr.txt"
HEADERS = {"User-Agent": "Mozilla/5.0 HistoryCafe-RAG/1.0 (educational, non-commercial)"}
BASE_API = "https://fr.wikisource.org/w/api.php"

PAGES_REMAINING = (
    [f"Mémorial_de_Sainte-Hélène_(1842)/Tome_1/Chapitre_{i:02d}" for i in range(10, 15)] +
    [f"Mémorial_de_Sainte-Hélène_(1842)/Tome_2/Chapitre_{i:02d}" for i in range(1, 22)] +
    [
        "Mémorial_de_Sainte-Hélène_(1842)/Tome_2/Récit_d'O'Meara",
        "Mémorial_de_Sainte-Hélène_(1842)/Tome_2/Récit_d'Antomarchi",
        "Mémorial_de_Sainte-Hélène_(1842)/Tome_2/Testament",
        "Mémorial_de_Sainte-Hélène_(1842)/Tome_2/Translation_aux_Invalides",
        "Mémorial_de_Sainte-Hélène_(1842)/Tome_2/Appendice",
    ]
)


def fetch_page_text(page_title: str) -> str:
    url = (
        BASE_API
        + "?action=parse"
        + "&page=" + urllib.request.quote(page_title)
        + "&prop=text&format=json&disablelimitreport=1"
    )
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 15 * (attempt + 1) + random.uniform(2, 5)
                print(f" [429 retry {attempt+1}, wait {wait:.0f}s]", end="", flush=True)
                time.sleep(wait)
            else:
                return f"[ERREUR: {e}]"
        except Exception as e:
            return f"[ERREUR: {e}]"
    else:
        return "[ERREUR: 429 max retries]"

    if "parse" not in data:
        return "[PAGE INTROUVABLE]"

    html = data["parse"]["text"]["*"]
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div[^>]*class="[^"]*headertemplate[^"]*"[^>]*>.*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div[^>]*class="[^"]*ws-noexport[^"]*"[^>]*>.*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</p>', '\n\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</div>', '\n', html, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', html)

    for old, new in [
        ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'), ('&nbsp;', ' '),
        ('&#160;', ' '), ('&quot;', '"'), ('&#39;', "'"), ('&laquo;', '«'),
        ('&raquo;', '»'), ('&mdash;', '—'), ('&ndash;', '–'), ('&hellip;', '…'),
        ('&#9668;', ''), ('&#9658;', ''), ('◄', ''), ('►', ''),
    ]:
        text = text.replace(old, new)

    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line in ('', 'book'):
            continue
        if re.match(r'^(Las Cases|Ernest Bourdin|Paris|Tome (I|II)|1842|VTome)', line):
            continue
        if line.startswith('.mw-parser'):
            continue
        lines.append(line)

    result = '\n'.join(lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def main():
    print(f"Reprise du scraping : {len(PAGES_REMAINING)} pages restantes")

    appended = []
    ok = 0
    for page in PAGES_REMAINING:
        label = page.split("/", 2)[-1] if "/" in page else page
        print(f"  → {label} ...", end="", flush=True)

        text = fetch_page_text(page)
        if "[ERREUR" in text or "PAGE INTROUVABLE" in text:
            print(f" {text}")
        else:
            print(f" {len(text)} chars")
            ok += 1

        block = f"\n{'=' * 60}\n# {label.replace('_', ' ')}\n{'=' * 60}\n\n{text}\n"
        appended.append(block)

        time.sleep(3 + random.uniform(0.5, 2))

    # Ajouter au fichier existant
    with open(OUTPUT, 'a', encoding='utf-8') as f:
        f.write('\n'.join(appended))

    import os
    kb = os.path.getsize(OUTPUT) // 1024
    print(f"\nFichier final : {OUTPUT}")
    print(f"Taille totale : {kb} KB ({ok}/{len(PAGES_REMAINING)} pages ajoutées)")


if __name__ == "__main__":
    main()
