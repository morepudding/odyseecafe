# OdyséeCafé

> Un café fictif où les plus grands esprits français reviennent à la vie — et tweetent.

OdyséeCafé est un projet d'IA où chaque personnalité est reconstituée par RAG (Retrieval-Augmented Generation) à partir de ses propres écrits. Chaque personnage publie sur Twitter/X en son nom, à la première personne, dans son style d'époque.

---

## Concept

Au **OdyséeCafé**, les morts ont WiFi.

Chaque personnage est une IA distincte :
- entraînée sur **ses propres textes** (corpus historique domaine public)
- dotée d'un **système prompt** qui ancre sa personnalité, son époque, sa façon de parler
- capable de **commenter l'actualité** dans son style propre
- et de **tweeter** depuis un vrai compte Twitter/X

L'objectif n'est pas la reconstitution historique fidèle — c'est la **polémique**, le **style**, le **choc des idées**.

---

## Personnages

| Personnage | Statut | Compte Twitter/X |
|---|---|---|
| **Napoléon Bonaparte** | ✅ Actif | — |
| Voltaire | 🔲 À faire | — |
| Molière | 🔲 À faire | — |
| Chateaubriand | 🔲 À faire | — |
| Charles Maurras | 🔲 À faire | — |
| Louis-Ferdinand Céline | 🔲 À faire | — |
| Robespierre | 🔲 À faire | — |
| Pierre-Joseph Proudhon | 🔲 À faire | — |
| Jacques Bainville | 🔲 À faire | — |

---

## Stack technique

| Composant | Outil |
|---|---|
| Langage | Python 3.14 |
| Base vectorielle | Supabase Postgres + pgvector |
| Embeddings | `nvidia/llama-nemotron-embed-vl-1b-v2:free` via OpenRouter |
| LLM | `deepseek/deepseek-v4-flash` via OpenRouter (configurable) |
| API LLM | [OpenRouter](https://openrouter.ai) |
| Publication | Tweepy + API Twitter/X v2 |

---

## Architecture RAG

```
corpus/*.txt
     │
     ▼
ingest.py ──► Supabase `rag_chunks`
                   │
                   ▼
query.py ──► N chunks les plus proches (recherche sémantique)
                   │
                   ▼
chat.py / twitter_bot.py ──► LLM (OpenRouter) ──► Tweet / Réponse
```

Chaque personnage a :
- son propre dossier `corpus/` de textes sources
- ses chunks indexes dans Supabase
- son propre system prompt

---

## Structure du projet

```
odyseecafe/
│
├── corpus/                  ← textes sources par personnage
├── src/
│   ├── ingest.py            ← indexation corpus → Supabase
│   ├── query.py             ← recherche sémantique
│   ├── chat.py              ← REPL interactif
│   ├── twitter_bot.py       ← publication Twitter/X
│   ├── daily_napoleon_tweet.py  ← tweet quotidien automatique
│   └── compare_models.py   ← benchmark multi-modèles
├── tests/
│   └── benchmark.md         ← historique des réponses par étape
├── .env.local               ← clés API (non committé)
├── requirements.txt
└── PROJET.md                ← journal de décision technique détaillé
```

---

## Installation

```bash
git clone https://github.com/morepudding/odyseecafe.git
cd odyseecafe
pip install -r requirements.txt
```

Créer un fichier `.env.local` à la racine :

```env
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=deepseek/deepseek-v4-flash

# Twitter/X (OAuth 2.0)
TWITTER_CLIENT_ID=...
TWITTER_CLIENT_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...
```

---

## Utilisation

**Lancer le chat interactif (Napoléon) :**
```bash
python src/chat.py
```

**Indexer un nouveau corpus :**
```bash
python src/ingest.py
```

**Configurer Supabase :**
1. Exécuter `supabase_rag.sql` dans le SQL Editor Supabase.
2. Ajouter `SUPABASE_URL` et `SUPABASE_SERVICE_ROLE_KEY` dans `.env.local`.
3. Lancer `python src/ingest.py --character napoleon` pour indexer un corpus.

Le même SQL crée aussi `editorial_dossiers`, l'historique cloud des dossiers
quotidiens. Une sauvegarde de sujet avec dossier rempli archive automatiquement
le snapshot du jour. Endpoints utiles :
```bash
GET  /api/dossiers
POST /api/dossiers
```

**Publier un tweet :**
```bash
python src/daily_napoleon_tweet.py
```

**Comparer plusieurs modèles LLM :**
```bash
python src/compare_models.py
```

---

## Méthodologie — comment on construit un personnage

Chaque personnage est ajouté en suivant ces étapes, validées une par une :

| # | Étape | Description |
|---|---|---|
| 1 | **RAG** | Corpus ingéré, recherche sémantique opérationnelle |
| 2 | **System Prompt** | Personnalité, ton, règles d'immersion |
| 3 | **Few-shot** | Exemples de formulations tirés du corpus |
| 4 | **Fine-tuning** | *(optionnel)* Affinage sur un dataset personnage |

La question de référence est posée à chaque étape pour mesurer le progrès.

---

## Licence

Code source : [MIT](LICENSE)  
Textes du corpus : domaine public

---

*OdyséeCafé — depuis 2025*
