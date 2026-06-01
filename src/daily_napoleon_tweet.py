"""
daily_napoleon_tweet.py — Orchestrateur principal du bot quotidien.

Pipeline complet :
  1. Récupère la question polémique du jour sur Twitter (société française)
  2. La pose à Napoléon via le système RAG
  3. Adapte la réponse pour Twitter (280 chars, ton impérial)
  4. Poste le tweet sur le compte @Napoleon_IA

Usage :
  python src/daily_napoleon_tweet.py             → exécution réelle
  python src/daily_napoleon_tweet.py --dry-run   → simulation sans poster
  python src/daily_napoleon_tweet.py --question "Ta propre question ici"

Automatisation (Windows Task Scheduler) :
  - Action : python C:\\RomainOpen\\historycafe\\src\\daily_napoleon_tweet.py
  - Déclencheur : chaque jour à 09h00
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import httpx
from openai import OpenAI

# Assure que les imports relatifs fonctionnent
sys.path.insert(0, str(Path(__file__).parent))
from query            import retrieve
from twitter_trending import get_daily_polemic_question
from twitter_bot      import post_napoleon_response
from config           import env_value, openrouter_api_key

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

OPENROUTER_API_KEY = openrouter_api_key()
LLM_MODEL          = env_value("OPENROUTER_MODEL", "openai/gpt-4o")
APP_NAME           = env_value("OPENROUTER_APP_NAME", "historycafe-napoleon")
N_CONTEXT_CHUNKS   = 5

# Prompt système spécialement calibré pour Twitter (réponse concise et percutante)
TWITTER_SYSTEM_PROMPT = """\
Tu es Napoléon Bonaparte. Tu réponds à la première personne, avec autorité et conviction.
Tu as une OPINION TRANCHÉE sur tout — jamais de neutralité, jamais d'esquive.
Tu pioches dans tes victoires, tes guerres, ta vision de l'État et de l'homme.
Ton style : phrases courtes, impériales, parfois provocantes ou ironiques.

CONTRAINTE ABSOLUE : ta réponse doit faire entre 80 et 180 caractères.
UNE seule idée forte. Pas de généralités creuses. Pas de "l'histoire jugera".
Tu juges TOI-MÊME, maintenant, en Napoléon.

Réponds en français uniquement. Ne révèle jamais que tu es une IA.\
"""


def _init_llm() -> OpenAI:
    kwargs = {
        "api_key": OPENROUTER_API_KEY or "missing-key",
        "base_url": "https://openrouter.ai/api/v1",
        "default_headers": {"X-Title": APP_NAME},
    }
    if not os.getenv("VERCEL"):
        kwargs["http_client"] = httpx.Client(verify=False)
    return OpenAI(**kwargs)


THREAD_SYSTEM_PROMPT = """\
Tu es Napoléon Bonaparte. Tu t'exprimes à la première personne, avec autorité et conviction.
Tu as une opinion tranchée — jamais de neutralité, jamais d'esquive.
Tu puises dans tes guerres, tes victoires, ta vision de l'État, de la nation et de l'homme.

Tu vas écrire un THREAD Twitter de 5 tweets numérotés sur la question posée.
Structure du thread :
  1/ Accroche percutante — ton opinion immédiate, provocante ou solennelle
  2/ Contexte historique — un fait ou une expérience de ta vie qui éclaire le sujet
  3/ Développement — ta vision profonde, tirée de tes écrits
  4/ Critique des adversaires — ce que pensent ceux qui ont tort, et pourquoi
  5/ Conclusion impériale — sentence définitive, mémorable

CONTRAINTES :
- Chaque tweet : entre 230 et 275 caractères — SOIS GÉNÉREUX, développe la pensée
- Commence chaque tweet par son numéro : "1/" "2/" "3/" "4/" "5/"
- Style : direct, impérial, parfois ironique
- Réponds en français uniquement
- Ne révèle jamais que tu es une IA
- Retourne UNIQUEMENT les 5 tweets, un par ligne, rien d'autre\
"""


def _style_instruction(mode: str = "balanced") -> str:
    if mode == "sharp":
        return (
            "Mode éditorial : plus tranchant. Donne une opinion nette, polémique, "
            "mais reste publiable et historiquement défendable."
        )
    if mode == "historical":
        return (
            "Mode éditorial : plus historique. Appuie davantage chaque tweet sur "
            "une référence, une expérience politique ou militaire, sans devenir scolaire."
        )
    return (
        "Mode éditorial : équilibré. Le thread doit être incarné, polémique, "
        "clair et publiable après validation humaine."
    )


def _format_sources(chunks: list[dict]) -> list[dict]:
    sources = []
    seen = set()
    for chunk in chunks:
        source = chunk["source"]
        if source in seen:
            continue
        seen.add(source)
        sources.append({
            "source": source,
            "distance": round(float(chunk["distance"]), 4),
            "excerpt": chunk["text"][:260].replace("\n", " ").strip(),
        })
    return sources


def napoleon_thread_result(question: str, mode: str = "balanced") -> dict:
    """
    Génère un thread de 5 tweets Napoléon sur la question, en utilisant le RAG.
    Retourne les tweets et les sources utilisées pour validation éditoriale.
    """
    llm    = _init_llm()
    chunks = retrieve(question, n_results=N_CONTEXT_CHUNKS)
    style_instruction = _style_instruction(mode)

    context = "\n\n---\n\n".join(
        f"[{c['source']}]\n{c['text'][:400]}" for c in chunks[:5]
    ) or "Aucun extrait RAG disponible : reste prudent, évite d'inventer des citations précises."

    messages = [
        {"role": "system", "content": THREAD_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Voici des extraits de tes propres écrits pour t'inspirer :\n\n{context}\n\n"
                f"---\n\n"
                f"Question : {question}\n\n"
                f"{style_instruction}\n\n"
                f"Écris le thread de 5 tweets."
            ),
        },
    ]

    response = llm.chat.completions.create(
        model       = LLM_MODEL,
        messages    = messages,
        temperature = 0.85,
        max_tokens  = 700,
    )
    raw = (response.choices[0].message.content or "").strip()

    # Parse : on extrait les blocs commençant par 1/ 2/ 3/ 4/ 5/.
    # Certains modèles ajoutent des retours ligne dans un tweet : on les replie.
    import re
    tweets = re.findall(r'(?ms)(?:^|\n)\s*(\d+/\s.*?)(?=\n\s*\d+/|\Z)', raw)
    tweets = [re.sub(r"\s+", " ", t).strip() for t in tweets if t.strip()]

    # Sécurité : si le LLM n'a pas respecté le format, on découpe naïvement
    if len(tweets) < 5:
        lines = [l.strip() for l in raw.split("\n") if l.strip()]
        tweets = lines[:5]

    # Tronque chaque tweet à 280 chars (hard limit X)
    result = []
    for i, t in enumerate(tweets[:5], 1):
        if len(t) > 280:
            cut = t.rfind(" ", 0, 278)
            t = (t[:cut] if cut != -1 else t[:278]) + "…"
        result.append(t)

    # Complète si moins de 5
    while len(result) < 5:
        result.append(f"{len(result)+1}/ — Napoléon Bonaparte")

    return {"tweets": result, "sources": _format_sources(chunks), "mode": mode}


def napoleon_thread(question: str, mode: str = "balanced") -> list[str]:
    """Rétrocompatibilité : retourne seulement la liste des tweets."""
    return napoleon_thread_result(question, mode=mode)["tweets"]


def napoleon_short_answer(question: str) -> str:
    """Retourne le premier tweet du thread (rétrocompatibilité)."""
    return napoleon_thread(question)[0]


def run(dry_run: bool = False, forced_question: str | None = None) -> None:
    """
    Exécute le pipeline complet.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*60}")
    print(f" NAPOLÉON DAILY TWEET — {timestamp}")
    print(f"{'='*60}\n")

    # Étape 1 — Question polémique du jour
    if forced_question:
        print(f"[MODE MANUEL] Question fournie : {forced_question}")
        question = forced_question
    else:
        print("ÉTAPE 1 — Recherche de la question polémique du jour...")
        question = get_daily_polemic_question()

    print(f"\n  ➜ Question : {question}\n")

    # Étape 2 — Réponse de Napoléon (RAG)
    print("ÉTAPE 2 — Génération de la réponse Napoléon (RAG)...")
    answer = napoleon_short_answer(question)
    print(f"\n  ➜ Réponse ({len(answer)} chars) :\n  {answer}\n")

    # Étape 3 — Post sur Twitter
    mode_label = "[DRY RUN]" if dry_run else "[LIVE]"
    print(f"ÉTAPE 3 — Publication sur Twitter {mode_label}...")
    tweets = post_napoleon_response(question, answer, dry_run=dry_run)

    print(f"\n✅ Terminé — {len(tweets)} tweet(s) {'simulé(s)' if dry_run else 'publié(s)'}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bot quotidien : Napoléon répond à la polémique française du jour"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simule sans poster sur Twitter",
    )
    parser.add_argument(
        "--question",
        type=str,
        default=None,
        help="Force une question spécifique au lieu de chercher sur Twitter",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run, forced_question=args.question)


if __name__ == "__main__":
    main()
