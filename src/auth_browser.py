"""
auth_browser.py — Flow OAuth1 avec callback (pas de PIN à copier).

Usage : python src/auth_browser.py
Le navigateur s'ouvre → tu cliques "Authorize" → terminé.
"""

import os
import sys
import re
import time
from pathlib import Path
from dotenv import load_dotenv, set_key
import tweepy

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

API_KEY    = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ENV_FILE   = Path(__file__).parent.parent / ".env.local"

CALLBACK = "https://x.com"


def update_env(token: str, secret: str):
    """Met à jour TWITTER_ACCESS_TOKEN et TWITTER_ACCESS_TOKEN_SECRET dans .env.local."""
    content = ENV_FILE.read_text(encoding="utf-8")

    def replace_or_add(text, key, value):
        pattern = rf"^{re.escape(key)}=.*$"
        if re.search(pattern, text, re.MULTILINE):
            return re.sub(pattern, f"{key}={value}", text, flags=re.MULTILINE)
        return text + f"\n{key}={value}"

    content = replace_or_add(content, "TWITTER_ACCESS_TOKEN", token)
    content = replace_or_add(content, "TWITTER_ACCESS_TOKEN_SECRET", secret)
    ENV_FILE.write_text(content, encoding="utf-8")
    print(f"[auth] .env.local mis à jour.")


def main():
    handler = tweepy.OAuth1UserHandler(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        callback=CALLBACK,
    )

    auth_url = handler.get_authorization_url()

    print()
    print("=" * 60)
    print(" AUTORISATION TWITTER — étape 1/2")
    print("=" * 60)
    print()
    print("Ouvre ce lien, connecte-toi avec @OdyseeCafe et clique Authorize :")
    print()
    print(f"  {auth_url}")
    print()
    print("Après l'autorisation, Twitter va rediriger vers x.com.")
    print("Copie l'URL complète de cette page de redirection (elle contient")
    print("oauth_token=... et oauth_verifier=...) et colle-la ici :")
    print()

    redirect_url = input("URL de redirection : ").strip()

    # Extraire oauth_verifier
    m = re.search(r"oauth_verifier=([^&]+)", redirect_url)
    if not m:
        print("[ERREUR] oauth_verifier introuvable dans l'URL.")
        sys.exit(1)

    verifier = m.group(1)

    print(f"\n[auth] Verifier extrait : {verifier}")
    print("[auth] Échange du verifier contre les tokens...")

    access_token, access_token_secret = handler.get_access_token(verifier)

    print(f"\n[auth] Nouveaux tokens obtenus !")
    print(f"  ACCESS_TOKEN        : {access_token}")
    print(f"  ACCESS_TOKEN_SECRET : {access_token_secret}")

    update_env(access_token, access_token_secret)

    print()
    print("=" * 60)
    print(" SUCCÈS — Tokens enregistrés dans .env.local")
    print(" Lance maintenant : python src/daily_napoleon_tweet.py --dry-run")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
