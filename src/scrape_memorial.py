#!/usr/bin/env python3
"""
Scrape le Mémorial de Sainte-Hélène (1842) depuis Wikisource FR.
Extrait le texte propre chapitre par chapitre via l'API Wikimedia.
"""
import urllib.request
import json
import re
import time
import random

OUTPUT = r"C:\RomainOpen\historycafe\corpus\las_cases_memorial_wikisource_fr.txt"
HEADERS = {"User-Agent": "Mozilla/5.0 HistoryCafe-RAG/1.0 (educational, non-commercial)"}

BASE_API = "https://fr.wikisource.org/w/api.php"

# Structure du Mémorial de Sainte-Hélène (1842) sur Wikisource
# Tome 1 : Préambule + Chapitres 01-14
# Tome 2 : Chapitres 01-21 + O'Meara + Antomarchi + Testament + Transfert + Appendice
PAGES_ALREADY_DONE = (
    ["Mémorial_de_Sainte-Hélène_(1842)/Tome_1/Préambule"] +
    [f"Mémorial_de_Sainte-Hélène_(1842)/Tome_1/Chapitre_{i:02d}" for i in range(1, 10)]
)

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

PAGES = PAGES_ALREADY_DONE + PAGES_REMAINING


def fetch_page_text(page_title: str) -> str:
    """Récupère le texte rendu d'une page Wikisource et le nettoie."""
    url = (
        BASE_API
        + "?action=parse"
        + "&page=" + urllib.request.quote(page_title)
        + "&prop=text&format=json&disablelimitreport=1"
    )
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 10 * (attempt + 1) + random.uniform(1, 3)
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

    # Extraire seulement le contenu de la div principale (mw-parser-output)
    # Supprimer les blocs de navigation, headertemplate, etc.
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)

    # Supprimer les éléments de navigation/template
    html = re.sub(r'<div[^>]*class="[^"]*headertemplate[^"]*"[^>]*>.*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div[^>]*class="[^"]*ws-noexport[^"]*"[^>]*>.*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div[^>]*class="[^"]*navigation[^"]*"[^>]*>.*?</div>', '', html, flags=re.DOTALL)

    # Convertir les <br> et <p> en sauts de ligne
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</p>', '\n\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</div>', '\n', html, flags=re.IGNORECASE)

    # Supprimer toutes les balises restantes
    text = re.sub(r'<[^>]+>', '', html)

    # Décoder les entités HTML courantes
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&#160;', ' ')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&laquo;', '«')
    text = text.replace('&raquo;', '»')
    text = text.replace('&mdash;', '—')
    text = text.replace('&ndash;', '–')
    text = text.replace('&hellip;', '…')
    text = text.replace('&#9668;', '')  # ◄ navigation
    text = text.replace('&#9658;', '')  # ► navigation
    text = text.replace('◄', '')
    text = text.replace('►', '')

    # Nettoyer les lignes
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        # Exclure les lignes de boilerplate
        if line in ('', 'book'):
            continue
        if re.match(r'^(Las Cases|Ernest Bourdin|Paris|Tome (I|II)|1842|VTome)', line):
            continue
        if line.startswith('.mw-parser'):
            continue
        lines.append(line)

    # Consolider les paragraphes
    result = '\n'.join(lines)
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result.strip()


def main():
    all_text = []
    all_text.append("MÉMORIAL DE SAINTE-HÉLÈNE")
    all_text.append("par le Comte de Las Cases")
    all_text.append("Édition Ernest Bourdin, 1842")
    all_text.append("Source : fr.wikisource.org")
    all_text.append("=" * 70)
    all_text.append("")

    ok_count = 0
    for page in PAGES:
        label = page.split("/", 2)[-1] if "/" in page else page
        print(f"  → {label} ...", end="", flush=True)

        text = fetch_page_text(page)
        if "[ERREUR" in text or "PAGE INTROUVABLE" in text:
            print(f" {text}")
        else:
            char_count = len(text)
            print(f" {char_count} chars")
            ok_count += 1

        all_text.append(f"\n{'=' * 60}")
        all_text.append(f"# {label.replace('_', ' ')}")
        all_text.append(f"{'=' * 60}\n")
        all_text.append(text)
        all_text.append("")

        time.sleep(2 + random.uniform(0.5, 1.5))  # Respecter le rate limiting Wikisource

    full_text = '\n'.join(all_text)

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(full_text)

    kb = len(full_text.encode('utf-8')) // 1024
    print(f"\nFichier écrit : {OUTPUT}")
    print(f"Taille : {kb} KB ({ok_count}/{len(PAGES)} pages récupérées)")


if __name__ == "__main__":
    main()
