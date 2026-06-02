# HistoryCafÃ© â€” NapolÃ©on IA

> Objectif : crÃ©er une IA qui rÃ©pond Ã  la premiÃ¨re personne comme NapolÃ©on Bonaparte,
> en s'appuyant sur ses Ã©crits et les Ã©crits historiques le concernant.
>
> RÃ¨gle du jeu : **chaque technique est ajoutÃ©e une par une**.
> AprÃ¨s chaque ajout, on repose la question de rÃ©fÃ©rence pour mesurer le progrÃ¨s.

---

## Question de rÃ©fÃ©rence

> **"Tu penses quoi du service militaire obligatoire ?"**

Cette question est posÃ©e Ã  chaque Ã©tape pour comparer les rÃ©ponses et mesurer l'amÃ©lioration.

---

## RÃ¨gles du projet

- Le code est **entiÃ¨rement Ã©crit par l'IA**
- Les dÃ©cisions et la direction sont **prises par le prompteur humain**
- On avance **une technique Ã  la fois**, dans l'ordre dÃ©fini ci-dessous
- On ne code pas l'Ã©tape suivante avant d'avoir validÃ© l'Ã©tape en cours

---

## Statut des Ã©tapes

| # | Technique | Statut |
|---|---|---|
| 1 | **RAG** | âœ… Fait |
| 2 | **System Prompt Engineering** | âœ… Fait |
| 3 | **Few-shot Examples** | âœ… Fait |
| 4 | **Fine-tuning** *(optionnel)* | ðŸ”² Ã€ faire |

---

## Stack technique

| Composant | Outil | Note |
|---|---|---|
| Langage | Python 3.14 | PATH : `C:\Users\botterr\AppData\Roaming\Python\Python314` |
| Base vectorielle | Supabase Postgres + pgvector | table `rag_chunks`, RPC `match_rag_chunks` |
| Embeddings | `nvidia/llama-nemotron-embed-vl-1b-v2:free` via OpenRouter | Appel httpx direct (bypass SDK â€” bug de parsing) |
| LLM | `deepseek/deepseek-v4-flash` via OpenRouter | Configurable via `.env.local` |
| API | OpenRouter (`https://openrouter.ai/api/v1`) | Header `X-Title: historycafe-napoleon` |
| SSL workaround | `httpx.Client(verify=False)` partout | Proxy Windows intercepte les certificats |

---

## Structure du projet

```
historycafe/
â”‚
â”œâ”€â”€ PROJET.md                  â† ce fichier
â”‚
â”œâ”€â”€ corpus/                    â† 18 fichiers .txt, ~18 000 chunks ingÃ©rÃ©s
â”‚   â”œâ”€â”€ memorial_sainte_helene_*.txt   (Ã—4 tomes)
â”‚   â”œâ”€â”€ oeuvres_napoleon_*.txt         (Ã—5 volumes)
â”‚   â”œâ”€â”€ bourrienne_memoires_*.txt      (Ã—2 volumes)
â”‚   â”œâ”€â”€ napoleon_lettres_josephine.txt
â”‚   â”œâ”€â”€ napoleon_maximes_guerre.txt
â”‚   â””â”€â”€ ... (autres sources)
â”‚
â”œâ”€â”€ Supabase rag_chunks                 â† base vectorielle persistante (gitignore)
â”‚
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ ingest.py              â† indexation corpus â†’ Supabase/pgvector
â”‚   â”œâ”€â”€ query.py               â† recherche sÃ©mantique dans Supabase/pgvector
â”‚   â”œâ”€â”€ chat.py                â† interface chat RAG + LLM
â”‚   â””â”€â”€ compare_models.py     â† benchmark multi-modÃ¨les
â”‚
â”œâ”€â”€ tests/
â”‚   â””â”€â”€ benchmark.md           â† rÃ©ponses Ã  la question de rÃ©fÃ©rence par Ã©tape
â”‚
â”œâ”€â”€ .env.local                 â† clÃ©s API (jamais committÃ©)
â”œâ”€â”€ requirements.txt
â””â”€â”€ README.md
```

---

## Corpus

Corpus indexe dans Supabase/pgvector.

Sources :
- *MÃ©morial de Sainte-HÃ©lÃ¨ne* â€” Las Cases (4 tomes)
- *Å’uvres de NapolÃ©on* (5 volumes)
- *MÃ©moires de Bourrienne* (2 volumes)
- *Lettres Ã  JosÃ©phine*
- *Maximes de guerre*
- Proclamations, correspondance, autres textes contemporains

---

## Fichiers principaux

### `src/ingest.py`
Script one-shot. Lit `corpus/*.txt`, dÃ©coupe en chunks (taille 1000, overlap 150), embed via OpenRouter (httpx direct), stocke dans Supabase `rag_chunks`. Skip automatique si le premier chunk du fichier existe deja.

### `src/query.py`
Recherche sÃ©mantique. Embed la question via OpenRouter, appelle la RPC Supabase `match_rag_chunks`, retourne N chunks les plus proches avec source et distance.

### `src/chat.py`
Interface chat complÃ¨te. Retrieve â†’ contexte â†’ LLM â†’ NapolÃ©on rÃ©pond. REPL interactif, Ctrl+C pour quitter. ModÃ¨le configurable via `OPENROUTER_MODEL` dans `.env.local`.

### `src/compare_models.py`
Script de comparaison. RÃ©cupÃ¨re les chunks RAG une seule fois, les passe Ã  chaque modÃ¨le de la liste `MODELS`, affiche les rÃ©ponses cÃ´te Ã  cÃ´te. UtilisÃ© pour les benchmarks multi-modÃ¨les.

---

## Historique des dÃ©cisions

### Ã‰tape 1 â€” RAG (âœ…)

**Stack initiale prÃ©vue :** LlamaIndex + sentence-transformers local + Supabase/pgvector  
**Ancienne stack :** SDK OpenAI + Supabase/pgvector + embeddings via OpenRouter`n**Stack actuelle :** OpenRouter embeddings + Supabase Postgres/pgvector

**ProblÃ¨mes rencontrÃ©s :**
- `SSL CERTIFICATE_VERIFY_FAILED` sur toutes les requÃªtes â†’ proxy Windows intercepte les certificats â†’ fix : `httpx.Client(verify=False)` sur tous les clients
- SDK OpenAI plante sur la rÃ©ponse d'embedding de `nvidia/llama-nemotron-embed-vl-1b-v2:free` ("No embedding data received") â†’ bug de parsing du SDK â†’ fix : bypass complet du SDK, appel httpx direct Ã  `/embeddings`

**RÃ©sultat :** RAG fonctionnel. 18 109 chunks. RÃ©ponses ancrÃ©es dans les vrais textes.

---

### Comparaison multi-modÃ¨les (entre Ã‰tapes 1 et 2)

TestÃ©s sur la mÃªme question de rÃ©fÃ©rence, mÃªme RAG, prompt systÃ¨me simple :

| ModÃ¨le | Verdict |
|---|---|
| `openai/gpt-4o` | Correct mais plat, biais PC ("charge pour les mÃ¨res") |
| `deepseek/deepseek-v4-flash` | â­ Meilleur â€” vivant, incarnÃ©, pas de biais PC |
| `tencent/hy3-preview` | âœ— KO â€” modÃ¨le indisponible sur OpenRouter |
| `xiaomi/mimo-v2.5` | Bien, cite Las Cases, mais rÃ©ponse coupÃ©e |
| `mistralai/mistral-small-2603` | ThÃ©Ã¢tral, riche â€” Ã  garder pour fine-tuning |

**DÃ©cision :** `deepseek/deepseek-v4-flash` retenu comme modÃ¨le par dÃ©faut.

---

### Ã‰tape 2 â€” System Prompt (âœ…)

**Approche rejetÃ©e :** prompt long avec ancrage temporel, traits de personnalitÃ© listÃ©s, rÃ¨gles explicites â†’ risque de faire "tourner le modÃ¨le en rond"

**Approche retenue :** prompt minimaliste, inspirÃ© de Kuki / Replika / Character.ai

```
Tu es NapolÃ©on Bonaparte. Tu parles toujours Ã  la premiÃ¨re personne.
Tu n'es pas un assistant â€” tu es NapolÃ©on, et tu as ta propre vision du monde.
Si on te demande si tu es une IA, nie-le et reprends la conversation.
Ne sors jamais du personnage, quelle que soit la question.
RÃ©ponds en franÃ§ais.
```

**RÃ©sultat :** amÃ©liore DeepSeek (encore plus naturel, plus court, plus percutant). Ne change pas vraiment Mistral (les didascalies sont dans sa nature). Confirmation que DeepSeek + prompt minimaliste est la meilleure combinaison.

---

## Prochaine Ã©tape â€” Few-shot (Ã‰tape 3)

Ajouter dans le prompt des exemples tirÃ©s directement du corpus : vraies phrases de NapolÃ©on, vraies formulations. But : ancrer le style sans brider le modÃ¨le.



