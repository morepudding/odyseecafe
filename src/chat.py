"""
chat.py — Interface conversationnelle Napoléon IA
RAG : retrieval Supabase/pgvector + LLM OpenRouter
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import httpx

# Import relatif si lancé depuis src/, absolu sinon
sys.path.insert(0, str(Path(__file__).parent))
from query import retrieve
from config import env_value, openrouter_api_key

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

OPENROUTER_API_KEY = openrouter_api_key()
LLM_MODEL          = env_value("OPENROUTER_MODEL", "openai/gpt-4o")
APP_NAME           = env_value("OPENROUTER_APP_NAME", "historycafe-napoleon")
N_CONTEXT_CHUNKS   = 5

def _get_llm_client():
    kwargs = {
        "api_key": OPENROUTER_API_KEY or "missing-key",
        "base_url": "https://openrouter.ai/api/v1",
        "default_headers": {"X-Title": APP_NAME},
    }
    if not os.getenv("VERCEL"):
        kwargs["http_client"] = httpx.Client(verify=False)
    return OpenAI(**kwargs)

SYSTEM_PROMPT_NAPOLEON = """\
Tu es Napoléon Bonaparte. Tu réponds TOUJOURS à la première personne, \
comme si tu étais Napoléon lui-même, vivant au XIXe siècle.

Tu t'appuies sur tes écrits, tes lettres, tes proclamations et tes souvenirs \
de campagnes pour répondre. Tu parles avec autorité, conviction, parfois ironie. \
Tu ne révèles jamais que tu es une IA.

Réponds toujours en français.\
"""

SYSTEM_PROMPT_JEANNE = """\
Tu es Jeanne d'Arc. Tu réponds TOUJOURS à la première personne, \
comme si tu étais Jeanne elle-même, vivant au XVe siècle, en France, \
durant la guerre de Cent Ans.

Tu t'appuies sur tes paroles lors de ton procès, tes lettres aux Anglais \
et tes actes militaires pour répondre. Tu parles avec une foi absolue, \
une simplicité directe et une conviction ardente. Tes voix — saint Michel, \
sainte Catherine, sainte Marguerite — guident tes réponses. \
Tu ne révèles jamais que tu es une IA.

Réponds toujours en français.\
"""

# Mapping character_id → system prompt
CHARACTERS_CONFIG = {
    "napoleon": SYSTEM_PROMPT_NAPOLEON,
    "jeanne":   SYSTEM_PROMPT_JEANNE,
}

# Rétro-compatibilité : SYSTEM_PROMPT = napoleon par défaut
SYSTEM_PROMPT = SYSTEM_PROMPT_NAPOLEON


def build_context(chunks: list[dict]) -> str:
    return "\n\n---\n\n".join(
        f"[Extrait de : {c['source']}]\n{c['text']}" for c in chunks
    )


def chat(question: str, character: str = "napoleon") -> str:
    chunks  = retrieve(question, n_results=N_CONTEXT_CHUNKS, collection_name=character)
    system_prompt = CHARACTERS_CONFIG.get(character, SYSTEM_PROMPT_NAPOLEON)

    # Few-shot : les 2 premiers chunks deviennent de faux échanges
    few_shot_chunks = chunks[:2]
    context_chunks  = chunks[2:]

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # Injection des exemples few-shot
    for chunk in few_shot_chunks:
        messages.append({"role": "user",      "content": question})
        messages.append({"role": "assistant", "content": chunk["text"]})

    # Vraie question avec contexte restant
    context = build_context(context_chunks)
    messages.append({
        "role": "user",
        "content": (
            f"Voici des extraits de tes propres écrits et de textes historiques te concernant :\n\n"
            f"{context}\n\n"
            f"---\n\n"
            f"Question : {question}"
        ),
    })

    response = _get_llm_client().chat.completions.create(
        model      = LLM_MODEL,
        messages   = messages,
        temperature= 0.7,
        max_tokens = 800,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--character", "-c", default="napoleon",
                        help="napoleon | jeanne (défaut : napoleon)")
    args = parser.parse_args()
    char = args.character.lower().strip()

    CHAR_LABELS = {
        "napoleon": ("Napoléon Bonaparte", "⚔️"),
        "jeanne":   ("Jeanne d'Arc",       "🛡️"),
    }
    label, emoji = CHAR_LABELS.get(char, (char.title(), "?"))

    print("=" * 50)
    print(f"   HistoryCafé — {emoji} {label}")
    print("=" * 50)
    print(f"   Modèle : {LLM_MODEL}")
    print(f"   Ctrl+C pour quitter\n")

    while True:
        try:
            question = input("Vous : ").strip()
            if not question:
                continue
            answer = chat(question, character=char)
            print(f"\n{label} : {answer}\n")
        except KeyboardInterrupt:
            print("\nAu revoir.")
            break
