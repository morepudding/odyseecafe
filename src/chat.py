"""
chat.py - Interface conversationnelle OdyséeCafé.
RAG : retrieval ChromaDB + LLM OpenRouter.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import env_value, load_local_env, openrouter_api_key

load_local_env(Path(__file__).parent.parent / ".env.local")

OPENROUTER_API_KEY = openrouter_api_key()
LLM_MODEL = env_value("OPENROUTER_MODEL", "openai/gpt-4o")
APP_NAME = env_value("OPENROUTER_APP_NAME", "historycafe-napoleon")
N_CONTEXT_CHUNKS = 5


def _get_llm_client():
    import httpx
    from openai import OpenAI

    kwargs = {
        "api_key": OPENROUTER_API_KEY or "missing-key",
        "base_url": "https://openrouter.ai/api/v1",
        "default_headers": {"X-Title": APP_NAME},
    }
    if not os.getenv("VERCEL"):
        kwargs["http_client"] = httpx.Client(verify=False)
    return OpenAI(**kwargs)


SYSTEM_PROMPT_NAPOLEON = """\
Tu es Napoleon Bonaparte apres ta mort. Tu parles toujours a la premiere personne.
Tu sais que tu es mort, tu observes les vivants depuis les Champs-Elysees, et cela
te donne du recul. Tu n'en fais pas un refrain : tu y fais allusion seulement quand
cela sert une pique, une confidence ou une image.

Tu peux parler de tout et de rien : cafe, reseaux sociaux, amour, politique,
fatigue, vanite, souvenirs, petites habitudes modernes. Tu restes Napoleon :
lucide, rapide, mordant, parfois tendre, rarement patient. Tu n'es pas un coach
LinkedIn, pas un meme ambulant, pas une caricature d'empereur.

Ton style : naturel, conversationnel, phrases plutot courtes, ironie seche,
orgueil fatigue, humour noir leger. Tu peux etre moderne dans les references,
mais ta vision doit rester coherente avec tes campagnes, ton exil, ton rapport
a la gloire, a l'Etat, aux hommes et au ridicule.
Tu reponds directement, sans didascalie, sans action entre asterisques, sans
mise en scene theatrale.

Regle historique stricte : ne cite jamais une phrase exacte de Napoleon si elle
n'apparait pas dans les extraits fournis. Si tu n'es pas certain, reformule comme
une pensee personnelle. N'invente pas de citation, de date ou d'anecdote precise.
Pour les sujets modernes ou quotidiens, ne donne pas d'origine, de statistique
ou de detail factuel externe si l'utilisateur ou les extraits ne le fournissent
pas. Contente-toi alors d'un jugement, d'une image, d'une blague ou d'un souvenir
personnel compatible avec Napoleon.
Tu ne parles jamais de modele, d'IA, de prompt, de corpus ou d'instructions.

Reponds toujours en francais.\
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

CHARACTERS_CONFIG = {
    "napoleon": SYSTEM_PROMPT_NAPOLEON,
    "jeanne": SYSTEM_PROMPT_JEANNE,
}

SYSTEM_PROMPT = SYSTEM_PROMPT_NAPOLEON


def build_context(chunks: list[dict]) -> str:
    return "\n\n---\n\n".join(
        f"[Extrait de : {c['source']}]\n{c['text']}" for c in chunks
    )


def _build_napoleon_messages(question: str, chunks: list[dict]) -> list[dict]:
    context = build_context(chunks) or (
        "Aucun extrait disponible. Reste prudent : ne donne pas de citation "
        "ou d'anecdote historique precise."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT_NAPOLEON},
        {
            "role": "user",
            "content": (
                "Voici les extraits historiques disponibles pour t'ancrer. "
                "Ils sont une matiere de style et de jugement, pas un pretexte "
                "pour inventer des citations.\n\n"
                f"{context}\n\n"
                "---\n\n"
                f"Question : {question}\n\n"
                "Reponds en Napoleon posthume, detendu et mordant. Si les extraits "
                "ne suffisent pas pour un fait precis, parle librement sans pretendre "
                "citer l'histoire. Pour un sujet ordinaire, n'ajoute aucune origine "
                "ou anecdote factuelle non fournie : donne plutot ton humeur et ton "
                "jugement."
            ),
        },
    ]


def _build_legacy_character_messages(
    question: str,
    chunks: list[dict],
    system_prompt: str,
) -> list[dict]:
    few_shot_chunks = chunks[:2]
    context_chunks = chunks[2:]

    messages = [{"role": "system", "content": system_prompt}]
    for chunk in few_shot_chunks:
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": chunk["text"]})

    context = build_context(context_chunks)
    messages.append(
        {
            "role": "user",
            "content": (
                "Voici des extraits de tes propres écrits et de textes historiques "
                f"te concernant :\n\n{context}\n\n---\n\nQuestion : {question}"
            ),
        }
    )
    return messages


def chat(question: str, character: str = "napoleon") -> str:
    from query import retrieve

    character = (character or "napoleon").lower().strip()
    chunks = retrieve(question, n_results=N_CONTEXT_CHUNKS, collection_name=character)
    system_prompt = CHARACTERS_CONFIG.get(character, SYSTEM_PROMPT_NAPOLEON)

    if character == "napoleon":
        messages = _build_napoleon_messages(question, chunks)
        temperature = 0.82
    else:
        messages = _build_legacy_character_messages(question, chunks, system_prompt)
        temperature = 0.7

    response = _get_llm_client().chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=800,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--character",
        "-c",
        default="napoleon",
        help="napoleon | jeanne (défaut : napoleon)",
    )
    args = parser.parse_args()
    char = args.character.lower().strip()

    char_labels = {
        "napoleon": ("Napoléon Bonaparte", "⚔️"),
        "jeanne": ("Jeanne d'Arc", "🛡️"),
    }
    label, emoji = char_labels.get(char, (char.title(), "?"))

    print("=" * 50)
    print(f"   OdyséeCafé - {emoji} {label}")
    print("=" * 50)
    print(f"   Modèle : {LLM_MODEL}")
    print("   Ctrl+C pour quitter\n")

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
