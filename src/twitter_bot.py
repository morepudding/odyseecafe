"""
twitter_bot.py — Poste des tweets depuis le compte Twitter de Napoléon.

Prérequis dans .env.local :
  TWITTER_API_KEY             → clé API de l'app Developer
  TWITTER_API_SECRET          → secret de l'app Developer
  TWITTER_ACCESS_TOKEN        → OAuth token du compte @Napoleon_IA
  TWITTER_ACCESS_TOKEN_SECRET → OAuth token secret du compte @Napoleon_IA

Limites Twitter :
  - 1 tweet = 280 caractères max
  - Si la réponse Napoléon est plus longue → on coupe intelligemment en thread (2 tweets)
"""

import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv
import tweepy

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

TWITTER_API_KEY             = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET          = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN        = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# OAuth 2.0 (plan B — contourne les restrictions Read Only d'OAuth 1.0a)
TWITTER_OAUTH2_ACCESS_TOKEN = os.getenv("TWITTER_OAUTH2_ACCESS_TOKEN")

TWEET_MAX_CHARS = 280
SIGNATURE       = "\n\n— Napoléon Bonaparte"


def _init_client():
    # Priorité : OAuth 2.0 (tweet.write scope explicite) > OAuth 1.0a
    if TWITTER_OAUTH2_ACCESS_TOKEN:
        return tweepy.Client(access_token=TWITTER_OAUTH2_ACCESS_TOKEN), "v2"

    missing = [
        name for name, val in {
            "TWITTER_API_KEY":             TWITTER_API_KEY,
            "TWITTER_API_SECRET":          TWITTER_API_SECRET,
            "TWITTER_ACCESS_TOKEN":        TWITTER_ACCESS_TOKEN,
            "TWITTER_ACCESS_TOKEN_SECRET": TWITTER_ACCESS_TOKEN_SECRET,
        }.items() if not val
    ]
    if missing:
        raise ValueError(
            f"Variables manquantes dans .env.local : {', '.join(missing)}\n"
            "Lance d'abord : python src/auth_setup_oauth2.py"
        )

    return tweepy.Client(
        consumer_key        = TWITTER_API_KEY,
        consumer_secret     = TWITTER_API_SECRET,
        access_token        = TWITTER_ACCESS_TOKEN,
        access_token_secret = TWITTER_ACCESS_TOKEN_SECRET,
    ), "v2"


def _split_into_tweets(question: str, answer: str) -> list[str]:
    """
    Construit 1 ou 2 tweets :
      - Tweet 1 : la question (hashtag #SociétéFrançaise) + début de réponse
      - Tweet 2 (si nécessaire) : suite de la réponse + signature
    """
    header    = f"❓ {question}\n\n"
    footer    = SIGNATURE
    available = TWEET_MAX_CHARS - len(header) - len(footer)

    if available >= len(answer):
        # Tout tient en un seul tweet
        return [f"{header}{answer}{footer}"]

    # Coupe proprement sur une phrase ou un espace
    cut_point = answer.rfind(". ", 0, available)
    if cut_point == -1:
        cut_point = answer.rfind(" ", 0, available)
    if cut_point == -1:
        cut_point = available

    part1 = answer[:cut_point + 1].strip()
    part2 = answer[cut_point + 1:].strip()

    tweet1 = f"{header}{part1}…"[:TWEET_MAX_CHARS]
    tweet2 = f"…{part2}{footer}"[:TWEET_MAX_CHARS]

    return [tweet1, tweet2]


def post_napoleon_response(question: str, answer: str, dry_run: bool = False) -> list[str]:
    """
    Poste la réponse de Napoléon sur Twitter.

    Args:
        question : la question polémique du jour
        answer   : la réponse générée par le RAG Napoléon
        dry_run  : si True, affiche les tweets sans les poster (pour tester)

    Returns:
        Liste des textes des tweets postés (ou simulés).
    """
    tweets = _split_into_tweets(question, answer)

    if dry_run:
        print("\n[DRY RUN] Tweets qui seraient postés :")
        for i, t in enumerate(tweets, 1):
            print(f"\n── Tweet {i}/{len(tweets)} ({len(t)} chars) ──")
            print(t)
        return tweets

    client, api_version = _init_client()
    last_id   = None

    for i, text in enumerate(tweets, 1):
        try:
            if last_id:
                resp = client.create_tweet(text=text, in_reply_to_tweet_id=last_id, user_auth=True)
            else:
                resp = client.create_tweet(text=text, user_auth=True)
            last_id = resp.data["id"]

            print(f"[twitter_bot] Tweet {i}/{len(tweets)} posté — id={last_id}")

        except tweepy.TweepyException as exc:
            print(f"[twitter_bot] Erreur lors du post du tweet {i}: {exc}", file=sys.stderr)
            raise

    return tweets


if __name__ == "__main__":
    # Test rapide en dry_run
    question = "Faut-il supprimer les retraites pour tous ?"
    answer   = (
        "La retraite est la récompense du service rendu à la nation ! "
        "Tout soldat, tout fonctionnaire mérite de finir ses jours dignement. "
        "Supprimer cela serait trahir ceux qui ont tout donné à la France."
    )
    post_napoleon_response(question, answer, dry_run=True)
