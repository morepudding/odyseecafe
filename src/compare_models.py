"""
compare_models.py — Teste la question benchmark sur plusieurs modèles et affiche les réponses côte à côte.
"""

import os, sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import httpx

sys.path.insert(0, str(Path(__file__).parent))
from query import retrieve

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

OPENROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
APP_NAME           = os.getenv("OPENROUTER_APP_NAME", "historycafe-napoleon")

MODELS = [
    "deepseek/deepseek-v4-flash",
    "mistralai/mistral-small-2603",
]

QUESTION = "Tu penses quoi du service militaire obligatoire ?"

SYSTEM_PROMPT = """\
Tu es Napoléon Bonaparte. Tu parles toujours à la première personne.
Tu n'es pas un assistant — tu es Napoléon, et tu as ta propre vision du monde.
Si on te demande si tu es une IA, nie-le et reprends la conversation.
Ne sors jamais du personnage, quelle que soit la question.
Réponds en français.\
"""

_http = httpx.Client(verify=False, timeout=60)


def ask_model(model: str, context: str, question: str) -> str:
    client = OpenAI(
        api_key         = OPENROUTER_API_KEY,
        base_url        = "https://openrouter.ai/api/v1",
        default_headers = {"X-Title": APP_NAME},
        http_client     = _http,
    )
    user_msg = f"""Voici des extraits de mes écrits et de témoignages me concernant :

{context}

---

Question : {question}"""

    resp = client.chat.completions.create(
        model       = model,
        messages    = [
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": user_msg},
        ],
        temperature = 0.7,
        max_tokens  = 600,
    )
    return resp.choices[0].message.content.strip()


def main():
    print(f"\nQuestion : « {QUESTION} »")
    print("Récupération des chunks RAG...")
    chunks = retrieve(QUESTION, n_results=5)
    context = "\n\n---\n\n".join(
        f"[{c['source']}]\n{c['text']}" for c in chunks
    )
    print(f"{len(chunks)} chunks récupérés.\n")
    print("=" * 70)

    results = {}
    for model in MODELS:
        print(f"\n▶ Modèle : {model}")
        print("-" * 70)
        try:
            answer = ask_model(model, context, QUESTION)
            results[model] = answer
            print(answer)
        except Exception as e:
            results[model] = f"ERREUR : {e}"
            print(f"ERREUR : {e}")
        print()

    # Résumé pour copier dans benchmark.md
    print("\n" + "=" * 70)
    print("RÉSUMÉ — copiable dans benchmark.md")
    print("=" * 70)
    for model, answer in results.items():
        print(f"\n### {model}\n{answer}\n")


if __name__ == "__main__":
    main()
