# HistoryCafé — Napoléon IA

> Objectif : créer une IA qui répond à la première personne comme Napoléon Bonaparte,
> en s'appuyant sur ses écrits et les écrits historiques le concernant.
>
> Règle du jeu : **chaque technique est ajoutée une par une**.
> Après chaque ajout, on repose la question de référence pour mesurer le progrès.

---

## Question de référence

> **"Tu penses quoi du service militaire obligatoire ?"**

Cette question est posée à chaque étape pour comparer les réponses et mesurer l'amélioration.

---

## Règles du projet

- Le code est **entièrement écrit par l'IA**
- Les décisions et la direction sont **prises par le prompteur humain**
- On avance **une technique à la fois**, dans l'ordre défini ci-dessous
- On ne code pas l'étape suivante avant d'avoir validé l'étape en cours

---

## Statut des étapes

| # | Technique | Statut |
|---|---|---|
| 1 | **RAG** | ✅ Fait |
| 2 | **System Prompt Engineering** | ✅ Fait |
| 3 | **Few-shot Examples** | ✅ Fait |
| 4 | **Fine-tuning** *(optionnel)* | 🔲 À faire |

---

## Stack technique

| Composant | Outil | Note |
|---|---|---|
| Langage | Python 3.14 | PATH : `C:\Users\botterr\AppData\Roaming\Python\Python314` |
| Base vectorielle | ChromaDB (local) | `chroma_db/`, collection `napoleon` |
| Embeddings | `nvidia/llama-nemotron-embed-vl-1b-v2:free` via OpenRouter | Appel httpx direct (bypass SDK — bug de parsing) |
| LLM | `deepseek/deepseek-v4-flash` via OpenRouter | Configurable via `.env.local` |
| API | OpenRouter (`https://openrouter.ai/api/v1`) | Header `X-Title: historycafe-napoleon` |
| SSL workaround | `httpx.Client(verify=False)` partout | Proxy Windows intercepte les certificats |

---

## Structure du projet

```
historycafe/
│
├── PROJET.md                  ← ce fichier
│
├── corpus/                    ← 18 fichiers .txt, ~18 000 chunks ingérés
│   ├── memorial_sainte_helene_*.txt   (×4 tomes)
│   ├── oeuvres_napoleon_*.txt         (×5 volumes)
│   ├── bourrienne_memoires_*.txt      (×2 volumes)
│   ├── napoleon_lettres_josephine.txt
│   ├── napoleon_maximes_guerre.txt
│   └── ... (autres sources)
│
├── chroma_db/                 ← base vectorielle persistante (gitignore)
│
├── src/
│   ├── ingest.py              ← indexation corpus → ChromaDB
│   ├── query.py               ← recherche sémantique dans ChromaDB
│   ├── chat.py                ← interface chat RAG + LLM
│   └── compare_models.py     ← benchmark multi-modèles
│
├── tests/
│   └── benchmark.md           ← réponses à la question de référence par étape
│
├── .env.local                 ← clés API (jamais committé)
├── requirements.txt
└── README.md
```

---

## Corpus

18 fichiers `.txt`, **18 109 chunks** ingérés dans ChromaDB.

Sources :
- *Mémorial de Sainte-Hélène* — Las Cases (4 tomes)
- *Œuvres de Napoléon* (5 volumes)
- *Mémoires de Bourrienne* (2 volumes)
- *Lettres à Joséphine*
- *Maximes de guerre*
- Proclamations, correspondance, autres textes contemporains

---

## Fichiers principaux

### `src/ingest.py`
Script one-shot. Lit `corpus/*.txt`, découpe en chunks (taille 1000, overlap 150), embed via OpenRouter (httpx direct), stocke dans ChromaDB. Skip automatique si le fichier a déjà été ingéré (`{stem}_chunk_0` check).

### `src/query.py`
Recherche sémantique. Embed la question via OpenRouter, query ChromaDB, retourne N chunks les plus proches avec source et distance.

### `src/chat.py`
Interface chat complète. Retrieve → contexte → LLM → Napoléon répond. REPL interactif, Ctrl+C pour quitter. Modèle configurable via `OPENROUTER_MODEL` dans `.env.local`.

### `src/compare_models.py`
Script de comparaison. Récupère les chunks RAG une seule fois, les passe à chaque modèle de la liste `MODELS`, affiche les réponses côte à côte. Utilisé pour les benchmarks multi-modèles.

---

## Historique des décisions

### Étape 1 — RAG (✅)

**Stack initiale prévue :** LlamaIndex + sentence-transformers local + ChromaDB  
**Stack réelle :** SDK OpenAI + ChromaDB + embeddings via OpenRouter

**Problèmes rencontrés :**
- `SSL CERTIFICATE_VERIFY_FAILED` sur toutes les requêtes → proxy Windows intercepte les certificats → fix : `httpx.Client(verify=False)` sur tous les clients
- SDK OpenAI plante sur la réponse d'embedding de `nvidia/llama-nemotron-embed-vl-1b-v2:free` ("No embedding data received") → bug de parsing du SDK → fix : bypass complet du SDK, appel httpx direct à `/embeddings`

**Résultat :** RAG fonctionnel. 18 109 chunks. Réponses ancrées dans les vrais textes.

---

### Comparaison multi-modèles (entre Étapes 1 et 2)

Testés sur la même question de référence, même RAG, prompt système simple :

| Modèle | Verdict |
|---|---|
| `openai/gpt-4o` | Correct mais plat, biais PC ("charge pour les mères") |
| `deepseek/deepseek-v4-flash` | ⭐ Meilleur — vivant, incarné, pas de biais PC |
| `tencent/hy3-preview` | ✗ KO — modèle indisponible sur OpenRouter |
| `xiaomi/mimo-v2.5` | Bien, cite Las Cases, mais réponse coupée |
| `mistralai/mistral-small-2603` | Théâtral, riche — à garder pour fine-tuning |

**Décision :** `deepseek/deepseek-v4-flash` retenu comme modèle par défaut.

---

### Étape 2 — System Prompt (✅)

**Approche rejetée :** prompt long avec ancrage temporel, traits de personnalité listés, règles explicites → risque de faire "tourner le modèle en rond"

**Approche retenue :** prompt minimaliste, inspiré de Kuki / Replika / Character.ai

```
Tu es Napoléon Bonaparte. Tu parles toujours à la première personne.
Tu n'es pas un assistant — tu es Napoléon, et tu as ta propre vision du monde.
Si on te demande si tu es une IA, nie-le et reprends la conversation.
Ne sors jamais du personnage, quelle que soit la question.
Réponds en français.
```

**Résultat :** améliore DeepSeek (encore plus naturel, plus court, plus percutant). Ne change pas vraiment Mistral (les didascalies sont dans sa nature). Confirmation que DeepSeek + prompt minimaliste est la meilleure combinaison.

---

## Prochaine étape — Few-shot (Étape 3)

Ajouter dans le prompt des exemples tirés directement du corpus : vraies phrases de Napoléon, vraies formulations. But : ancrer le style sans brider le modèle.


