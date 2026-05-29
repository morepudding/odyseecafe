"""
auth_setup.py — Génère les Access Tokens OAuth 1.0a via le navigateur.

Lance ce script UNE SEULE FOIS pour obtenir les tokens du compte @historycafe.
Il te donnera les valeurs à coller dans .env.local.

Usage :
  python src/auth_setup.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import tweepy

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

API_KEY    = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")

if not API_KEY or not API_SECRET:
    print("❌ TWITTER_API_KEY ou TWITTER_API_SECRET manquant dans .env.local")
    exit(1)

# OAuth 1.0a — mode PIN (pas besoin de callback URL)
oauth1_handler = tweepy.OAuth1UserHandler(
    consumer_key    = API_KEY,
    consumer_secret = API_SECRET,
    callback        = "oob",   # "out of band" = mode PIN
)

# Génère l'URL d'autorisation
auth_url = oauth1_handler.get_authorization_url()

print("\n" + "="*60)
print(" AUTORISATION TWITTER — @historycafe")
print("="*60)
print("\n1. Ouvre ce lien dans ton navigateur :\n")
print(f"   {auth_url}")
print("\n2. Connecte-toi avec le compte @historycafe")
print("3. Autorise l'application")
print("4. Twitter affiche un code PIN à 7 chiffres")
print("\n" + "="*60)

pin = input("\nColle le PIN ici : ").strip()

# Échange le PIN contre les tokens définitifs
oauth1_handler.get_access_token(pin)

access_token        = oauth1_handler.access_token
access_token_secret = oauth1_handler.access_token_secret

print("\n" + "="*60)
print(" ✅ TOKENS GÉNÉRÉS — colle-les dans .env.local")
print("="*60)
print(f"\nTWITTER_ACCESS_TOKEN={access_token}")
print(f"TWITTER_ACCESS_TOKEN_SECRET={access_token_secret}")
print("\n" + "="*60)

# Vérifie que ça marche
print("\nVérification du compte...")
client = tweepy.Client(
    consumer_key        = API_KEY,
    consumer_secret     = API_SECRET,
    access_token        = access_token,
    access_token_secret = access_token_secret,
)
me = client.get_me()
print(f"✅ Connecté en tant que : @{me.data.username} ({me.data.name})")
print("\nTu peux maintenant lancer : python src/daily_napoleon_tweet.py --dry-run")
