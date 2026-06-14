# OdyséeCafé - Napoléon IA

> Objectif actuel : créer un Napoléon conversationnel, posthume, détendu et
> mordant, capable de parler de tout et de rien en restant ancré dans le corpus
> historique complet.

## Direction Produit

La surface active est le chat. La génération de tweets, threads et automatisations
X est sortie du produit.

Le Napoléon actuel :

- parle toujours à la première personne ;
- sait qu'il est mort, sans en faire un refrain ;
- observe le monde moderne avec recul et ironie ;
- peut parler de sujets quotidiens comme de sujets historiques ;
- utilise le RAG pour s'ancrer, mais ne prétend pas citer si les extraits ne le permettent pas ;
- ne révèle jamais qu'il est une IA.

## Stack

| Composant | Outil |
|---|---|
| Langage | Python |
| Web app | Flask |
| Déploiement | Vercel |
| RAG production | Supabase pgvector |
| Embeddings | `nvidia/llama-nemotron-embed-vl-1b-v2:free` via OpenRouter |
| LLM | `deepseek/deepseek-v4-flash` via OpenRouter, configurable |

Sur Vercel, le backend RAG est Supabase. Le code ne doit pas répondre avec un
fallback approximatif si Supabase n'est pas configuré.

## Corpus Napoléon

Sources principales :

- Mémorial de Sainte-Hélène ;
- Oeuvres de Napoléon ;
- Mémoires de Bourrienne ;
- Journal de Gourgaud ;
- Mémoires de Méneval ;
- lettres à Joséphine ;
- maximes de guerre.

Le gisement le plus utile pour la nouvelle voix est Sainte-Hélène : humeur
variable, journaux, médecins, sarcasme, recul sur la mort et rapport au ridicule.

## RAG

```text
corpus/napoleon/*.txt
  -> src/ingest_supabase.py
  -> Supabase public.rag_chunks
  -> public.match_rag_chunks()
  -> src/query.py
  -> src/chat.py
```

La migration SQL vit dans `supabase/migrations/20260613_rag_pgvector.sql`.

## Prompt Actuel

Le prompt Napoléon vit dans `src/chat.py`.

Intentions :

- moins solennel ;
- plus conversationnel ;
- humour sec ;
- conscience posthume occasionnelle ;
- liberté de sujets ;
- garde-fou strict contre les fausses citations.

## Commandes

```bash
npm run db:link
npm run db:push
npm run rag:ingest
python src/query.py --character napoleon "Que penses-tu de Sainte-Hélène ?"
python src/webapp.py
python src/chat.py
python src/compare_models.py
```

## Tests De Voix

Questions utiles pour valider le profil :

- Tu penses quoi des croissants ?
- Raconte-moi ta journée là-haut.
- Que penses-tu d'Instagram ?
- T'as déjà regretté Waterloo ?
- Tu préfères un café ou un chocolat chaud ?
- Donne-moi un conseil nul mais impérial.
- Parle-moi de Joséphine sans être dramatique.

Critères :

- français naturel ;
- Napoléon reconnaissable ;
- ton détente mais pas absurde ;
- humour mordant sans caricature ;
- pas de fausses citations ;
- pas de mention d'IA.
