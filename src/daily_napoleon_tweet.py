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

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

OPENROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
LLM_MODEL          = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
APP_NAME           = os.getenv("OPENROUTER_APP_NAME", "historycafe-napoleon")
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
    return OpenAI(
        api_key         = OPENROUTER_API_KEY,
        base_url        = "https://openrouter.ai/api/v1",
        default_headers = {"X-Title": APP_NAME},
        http_client     = httpx.Client(verify=False),
    )


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


def napoleon_thread(question: str) -> list[str]:
    """
    Génère un thread de 5 tweets Napoléon sur la question, en utilisant le RAG.
    Retourne une liste de 5 strings.
    """
    llm    = _init_llm()
    chunks = retrieve(question, n_results=N_CONTEXT_CHUNKS)

    context = "\n\n---\n\n".join(
        f"[{c['source']}]\n{c['text'][:400]}" for c in chunks[:5]
    )

    messages = [
        {"role": "system", "content": THREAD_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Voici des extraits de tes propres écrits pour t'inspirer :\n\n{context}\n\n"
                f"---\n\n"
                f"Question : {question}\n\n"
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

    # Parse : on extrait les lignes commençant par 1/ 2/ 3/ 4/ 5/
    import re
    tweets = re.findall(r'(?:^|\n)\s*(\d+/[^\n]+)', raw)
    tweets = [t.strip() for t in tweets if t.strip()]

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

    return result


def napoleon_short_answer(question: str) -> str:
    """Retourne le premier tweet du thread (rétrocompatibilité)."""
    return napoleon_thread(question)[0]

    return answer


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
