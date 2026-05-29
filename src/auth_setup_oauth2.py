"""
auth_setup_oauth2.py — Authentification OAuth 2.0 PKCE (plan B).

Contourne le problème de permissions OAuth 1.0a en demandant explicitement
le scope tweet.write via OAuth 2.0.

Prérequis dans .env.local :
  TWITTER_CLIENT_ID     → "Client ID" (OAuth 2.0) dans Keys and tokens
  TWITTER_CLIENT_SECRET → "Client Secret" (OAuth 2.0) dans Keys and tokens

Usage :
  python src/auth_setup_oauth2.py
"""

import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from dotenv import load_dotenv, set_key
import tweepy

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

CLIENT_ID     = os.getenv("TWITTER_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
ENV_FILE      = Path(__file__).parent.parent / ".env.local"

REDIRECT_URI  = "http://localhost:8080/callback"
SCOPES        = ["tweet.read", "tweet.write", "users.read", "offline.access"]

# Variable partagée pour capturer le code OAuth2
_auth_code = None
_server_done = threading.Event()


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"""
                <html><body style='font-family:sans-serif;text-align:center;padding:50px'>
                <h2>&#x2705; Autorisation r&#233;ussie !</h2>
                <p>Tu peux refermer cet onglet et retourner dans le terminal.</p>
                </body></html>
            """)
            _server_done.set()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Erreur : code OAuth2 manquant")

    def log_message(self, format, *args):
        pass  # Silence les logs HTTP


def run_callback_server():
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.timeout = 120  # 2 min max pour autoriser
    while not _server_done.is_set():
        server.handle_request()
    server.server_close()


if not CLIENT_ID or not CLIENT_SECRET:
    print("\n❌ Il manque TWITTER_CLIENT_ID et/ou TWITTER_CLIENT_SECRET dans .env.local")
    print("\nOù les trouver (même si le portail bug) :")
    print("  → Essaie depuis ton téléphone : developer.twitter.com")
    print("  → Onglet 'Keys and tokens' → section 'OAuth 2.0 Client ID and Client Secret'")
    print("  → Ajoute dans .env.local :")
    print("      TWITTER_CLIENT_ID=xxx")
    print("      TWITTER_CLIENT_SECRET=xxx")
    sys.exit(1)

handler = tweepy.OAuth2UserHandler(
    client_id    = CLIENT_ID,
    redirect_uri = REDIRECT_URI,
    scope        = SCOPES,
    client_secret= CLIENT_SECRET,
)

auth_url = handler.get_authorization_url()

print("\n" + "="*60)
print(" AUTORISATION TWITTER OAuth 2.0 — @OdyseeCafe")
print("="*60)
print("\nOuverture automatique du navigateur...")
print(f"(Si ça n'ouvre pas : {auth_url})")
print("\nConnecte-toi avec @OdyseeCafe et autorise l'app.")
print("="*60 + "\n")

# Lance le serveur callback en arrière-plan
t = threading.Thread(target=run_callback_server, daemon=True)
t.start()

# Ouvre le navigateur automatiquement
webbrowser.open(auth_url)

# Attend que l'utilisateur ait autorisé (max 2 min)
_server_done.wait(timeout=120)

if not _auth_code:
    print("❌ Timeout — aucune autorisation reçue en 2 minutes.")
    sys.exit(1)

# Échange le code contre les tokens
print("Échange du code contre les tokens...")
tokens = handler.fetch_token(f"{REDIRECT_URI}?code={_auth_code}&state=state")

access_token  = tokens["access_token"]
refresh_token = tokens.get("refresh_token", "")

# Sauvegarde dans .env.local
set_key(str(ENV_FILE), "TWITTER_OAUTH2_ACCESS_TOKEN",  access_token)
set_key(str(ENV_FILE), "TWITTER_OAUTH2_REFRESH_TOKEN", refresh_token)

print("\n" + "="*60)
print(" ✅ TOKENS OAuth 2.0 sauvegardés dans .env.local")
print("="*60)

# Vérifie le compte
client = tweepy.Client(access_token=access_token)
me = client.get_me()
print(f"\n✅ Connecté : @{me.data.username} ({me.data.name})")
print("\nRelance : python src/daily_napoleon_tweet.py --dry-run")
