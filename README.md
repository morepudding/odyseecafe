# OdyséeCafé

> Un café fictif où les grands morts reviennent discuter avec les vivants.

OdyséeCafé est une application de chat RAG. Le personnage actif est un Napoléon
posthume, détendu et mordant, capable de parler de sujets quotidiens tout en
restant ancré dans un corpus historique.

## Stack

| Composant | Outil |
|---|---|
| Web app | Flask |
| Déploiement | Vercel |
| RAG production | Supabase pgvector |
| Embeddings | `nvidia/llama-nemotron-embed-vl-1b-v2:free` via OpenRouter |
| LLM | `deepseek/deepseek-v4-flash` via OpenRouter, configurable |

Sur Vercel, le backend RAG est forcé sur Supabase. Si `SUPABASE_URL` ou
`SUPABASE_SERVICE_ROLE_KEY` manque, le chat échoue explicitement au lieu de
répondre sans corpus.

## Architecture RAG

```text
corpus/napoleon/*.txt
  -> src/ingest_supabase.py
  -> Supabase public.rag_chunks + match_rag_chunks()
  -> src/query.py
  -> src/chat.py
  -> src/webapp.py
```

Le chat récupère les meilleurs extraits du corpus, les transmet au modèle, puis
demande une réponse incarnée sans inventer de fausses citations historiques.

## Installation

```bash
pip install -r requirements.txt
```

Créer `.env.local` à la racine :

```env
OPEN_ROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=deepseek/deepseek-v4-flash
OPENROUTER_APP_NAME=odyseecafe-napoleon
OPENROUTER_EMBED_MODEL=nvidia/llama-nemotron-embed-vl-1b-v2:free

RAG_BACKEND=supabase
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Supabase

Le projet utilise Supabase CLI en dépendance dev locale (`supabase` dans
`package.json`) pour pousser les migrations SQL.

1. Authentifier le CLI :

```bash
set SUPABASE_ACCESS_TOKEN=sbp_...
```

2. Lier le projet distant :

```bash
npm run db:link
```

3. Vérifier puis appliquer la migration :

```bash
npm run db:push:dry-run
npm run db:push
```

4. Ingérer le corpus :

```bash
npm run rag:ingest
```

Le script ne ré-embedde pas les chunks déjà à jour. Pour forcer une réingestion :

```bash
python src/ingest_supabase.py --character napoleon --force
```

## Utilisation

Lancer l'interface web :

```bash
python src/webapp.py
```

Lancer le chat terminal :

```bash
python src/chat.py
```

Tester la recherche RAG :

```bash
python src/query.py --character napoleon "Que penses-tu de Sainte-Hélène ?"
```

## Structure

```text
odyseecafe/
├── api/index.py
├── corpus/                  textes sources par personnage
├── src/
│   ├── chat.py              prompt + orchestration RAG
│   ├── ingest_supabase.py   corpus -> Supabase pgvector
│   ├── query.py             retrieval Supabase/locale
│   └── webapp.py            interface Flask
├── supabase/migrations/
├── requirements.txt
└── PROJET.md
```

## Licence

Code source : MIT.
Textes du corpus : domaine public.
