"""
twitter_trending.py — Trouve la question polémique de la société française du jour sur Twitter/X.

Étapes :
  1. Cherche les tweets viraux en France sur des sujets de société (politique, social, culture...)
  2. Envoie les titres/tweets au LLM pour extraire LA question polémique du jour
  3. Retourne la question sous forme de string, prête à être posée à Napoléon

Prérequis :
  - TWITTER_BEARER_TOKEN dans .env.local  (compte Developer Twitter gratuit)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import tweepy
import httpx
from openai import OpenAI
from config import openrouter_api_key

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
OPENROUTER_API_KEY   = openrouter_api_key()
LLM_MODEL            = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
APP_NAME             = os.getenv("OPENROUTER_APP_NAME", "historycafe-napoleon")

# Mots-clés qui signalent un débat de société chaud en France
SOCIETY_KEYWORDS = [
    "immigration France",
    "retraites France",
    "école France polémique",
    "identité nationale France",
    "liberté expression France",
    "justice France scandale",
    "politique française débat",
    "société française crise",
    "France controverse",
    "tabou France 2024",
]

MAX_TWEETS_PER_QUERY = 10   # tweets récupérés par mot-clé
MAX_TOTAL_TWEETS     = 30   # total transmis au LLM


def _init_twitter_client() -> tweepy.Client:
    if not TWITTER_BEARER_TOKEN:
        raise ValueError(
            "TWITTER_BEARER_TOKEN manquant dans .env.local\n"
            "Crée un compte Developer sur https://developer.twitter.com et copie le Bearer Token."
        )
    return tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN, wait_on_rate_limit=True)


def _init_llm_client() -> OpenAI:
    kwargs = {
        "api_key": OPENROUTER_API_KEY,
        "base_url": "https://openrouter.ai/api/v1",
        "default_headers": {"X-Title": APP_NAME},
    }
    if not os.getenv("VERCEL"):
        kwargs["http_client"] = httpx.Client(verify=False)
    return OpenAI(**kwargs)


def fetch_viral_tweets(client: tweepy.Client) -> list[str]:
    """Cherche les tweets récents et viraux sur des sujets de société française."""
    tweets_collected: list[str] = []

    for keyword in SOCIETY_KEYWORDS:
        if len(tweets_collected) >= MAX_TOTAL_TWEETS:
            break
        try:
            query = (
                f"{keyword} lang:fr -is:retweet -is:reply"
                f" (has:hashtags OR min_faves:50)"
            )
            response = client.search_recent_tweets(
                query         = query,
                max_results   = MAX_TWEETS_PER_QUERY,
                tweet_fields  = ["public_metrics", "text"],
                sort_order    = "relevancy",
            )
            if response.data:
                for tweet in response.data:
                    tweets_collected.append(tweet.text.strip())
        except tweepy.TweepyException as exc:
            # Rate limit ou quota dépassé → on continue avec ce qu'on a
            print(f"[twitter_trending] Avertissement pour '{keyword}': {exc}", file=sys.stderr)
            continue

    return tweets_collected[:MAX_TOTAL_TWEETS]


def extract_polemic_question(tweets: list[str], llm_client: OpenAI) -> str:
    """
    Demande au LLM d'identifier LA question de société la plus polémique
    parmi les tweets collectés, et de la formuler comme une vraie question.
    """
    if not tweets:
        return "Quel est le principal défi de la société française aujourd'hui ?"

    tweets_sample = "\n".join(f"- {t}" for t in tweets)

    prompt = f"""Voici des tweets récents sur des sujets de société française :

{tweets_sample}

Identifie LE sujet le plus polémique, controversé ou débattu du moment.
Formule-le comme une question directe et provocatrice (max 150 caractères),
comme si on allait la poser à quelqu'un pour avoir son opinion franche.
La question doit être en français.

Réponds UNIQUEMENT avec la question, rien d'autre."""

    response = llm_client.chat.completions.create(
        model       = LLM_MODEL,
        messages    = [{"role": "user", "content": prompt}],
        temperature = 0.4,
        max_tokens  = 100,
    )
    question = response.choices[0].message.content.strip().strip('"').strip("'")
    return question


def get_daily_polemic_question() -> str:
    """
    Point d'entrée principal.
    Retourne la question polémique du jour sur la société française.
    """
    twitter  = _init_twitter_client()
    llm      = _init_llm_client()

    print("[1/2] Récupération des tweets viraux en France...")
    tweets = fetch_viral_tweets(twitter)
    print(f"      {len(tweets)} tweets collectés.")

    print("[2/2] Extraction de la question polémique du jour...")
    question = extract_polemic_question(tweets, llm)
    print(f"      Question : {question}")

    return question


if __name__ == "__main__":
    q = get_daily_polemic_question()
    print(f"\n📌 Question polémique du jour :\n{q}")
