# Corpus — HistoryCafé Napoleon IA

> **Structure des dossiers** : `corpus/napoleon/` pour Napoléon, `corpus/jeanne/` pour Jeanne d'Arc.
> Chaque personnage a sa propre collection ChromaDB (`napoleon`, `jeanne`).

---

## JEANNE D'ARC

### Ingestion
```bash
python src/ingest.py --character jeanne
```

### Sources disponibles (`corpus/jeanne/`)

| Fichier | Langue | Taille | Source | Contenu |
|---------|--------|--------|--------|---------|
| `twain_joan_of_arc_EN.txt` | EN | ~1.2 MB | Gutenberg #2489 | Mark Twain — *Personal Recollections of Joan of Arc* — roman historique très documenté, inclut des extraits du procès |
| `lowell_joan_of_arc_EN.txt` | EN | ~347 KB | Gutenberg #16766 | Francis C. Lowell — *Joan of Arc* — biographie savante EN |
| `michelet_jeanne_arc_fr.txt` | FR | ~113 KB | Gutenberg #3730 | Jules Michelet — *Jeanne d'Arc* — FR, texte classique |

**URLs de téléchargement :**
- Twain EN : `https://www.gutenberg.org/cache/epub/2489/pg2489.txt`
- Lowell EN : `https://www.gutenberg.org/cache/epub/16766/pg16766.txt`
- Michelet FR : `https://www.gutenberg.org/cache/epub/3730/pg3730.txt`

### Sources à ajouter (⏳ 503 Archive.org au 01/06/2026)

| Fichier cible | Source | Contenu |
|---|---|---|
| `proces_condamnation_quicherat_fr.txt` | Archive.org `procsdecondamnat00jean` | Procès de condamnation 1431 — SOURCE PRIMAIRE EXCEPTIONNELLE (paroles de Jeanne sous serment) |
| `proces_rehabilitation_fabre_fr.txt` | Archive.org `lesprcderhabi00fabr` | Procès en réhabilitation 1456 — témoignages contemporains |

**URLs alternatives à réessayer :**
- `https://archive.org/download/procsdecondamnat00jean/procsdecondamnat00jean_djvu.txt`
- `https://archive.org/download/lesprcderhabi00fabr/lesprcderhabi00fabr_djvu.txt`
- Script : `python src/download_jeanne_corpus.py`

---

## NAPOLÉON BONAPARTE

### Ingestion
```bash
python src/ingest.py --character napoleon   # ou sans argument (défaut)
```



| Fichier | Langue | Taille | Source | Contenu |
|---------|--------|--------|--------|---------|
| `oeuvres_napoleon_tome1_fr.txt` | FR | ~1133 KB | Gutenberg #12230 | Œuvres complètes Tome I — proclamations, lettres, campagne d'Italie |
| `oeuvres_napoleon_tome2_fr.txt` | FR | ~830 KB | Gutenberg #12782 | Œuvres complètes Tome II — lettres et correspondance 1797+ |
| `oeuvres_napoleon_tome3_fr.txt` | FR | ~314 KB | Gutenberg #12893 | Œuvres complètes Tome III |
| `oeuvres_napoleon_tome4_fr.txt` | FR | ~842 KB | Gutenberg #13192 | Œuvres complètes Tome IV |
| `oeuvres_napoleon_tome5_fr.txt` | FR | ~624 KB | Gutenberg #13475 | Œuvres complètes Tome V — Campagne de Russie 1812 |
| `napoleon_tendresses_imperiales_fr.txt` | FR | ~143 KB | Gutenberg #19700 | Lettres intimes à Joséphine et Marie Walewska (FR) |
| `napoleon_letters_josephine_EN.txt` | EN | ~603 KB | Gutenberg #37499 | Napoleon's Letters to Josephine 1796–1812 (EN, trad. Hall) |
| `napoleon_appeal_british_nation_EN.txt` | EN | ~44 KB | Gutenberg #50118 | Napoleon's Appeal to the British Nation (dicté à Sainte-Hélène, EN) |
| `napoleon_maxims_war_EN.txt` | EN | ~154 KB | Gutenberg #50750 | Maximes de guerre (EN) |

**URLs de téléchargement direct :**
- Tome II : `https://www.gutenberg.org/cache/epub/12782/pg12782.txt`
- Tome V : `https://www.gutenberg.org/cache/epub/13475/pg13475.txt`
- Tendresses impériales FR : `https://www.gutenberg.org/cache/epub/19700/pg19700.txt`
- Lettres à Joséphine EN : `https://www.gutenberg.org/cache/epub/37499/pg37499.txt`
- Appeal to British Nation EN : `https://www.gutenberg.org/cache/epub/50118/pg50118.txt`

---

## CATÉGORIE 2 — Témoignages directs (personnes qui ont côtoyé Napoléon)

### Mémorial de Sainte-Hélène — Las Cases (SOURCE PRIMAIRE EXCEPTIONNELLE)
> Napoléon dicte ses mémoires, Las Cases transcrit. Source de voix directe.

| Fichier | Langue | Taille | Source | Contenu |
|---------|--------|--------|--------|---------|
| `las_cases_memorial_tome1_fr.txt` | FR | ~665 KB | Archive.org `mmorialdesaint01lasc` | Mémorial Tome 1 — FR, OCR 1823, Univ. of Toronto |
| `las_cases_memorial_tome2_fr.txt` | FR | ~618 KB | Archive.org `mmorialdesaint02lasc` | Mémorial Tome 2 — FR, OCR 1823 |
| `las_cases_memorial_vol1_EN.txt` | EN | ~883 KB | Gutenberg #53967 | Memorial Vol. I (EN) |
| `las_cases_memorial_vol2_EN.txt` | EN | ~869 KB | Gutenberg #53968 | Memorial Vol. II (EN) |
| `las_cases_memorial_vol3_EN.txt` | EN | ~881 KB | Gutenberg #53969 | Memorial Vol. III (EN) |
| `las_cases_memorial_vol4_EN.txt` | EN | ~1014 KB | Gutenberg #53970 | Memorial Vol. IV (EN) |

**URLs de téléchargement direct :**
- Mémorial Tome 1 FR : `https://archive.org/download/mmorialdesaint01lasc/mmorialdesaint01lasc_djvu.txt`
- Mémorial Tome 2 FR : `https://archive.org/download/mmorialdesaint02lasc/mmorialdesaint02lasc_djvu.txt`
- Las Cases Vol I EN : `https://www.gutenberg.org/cache/epub/53967/pg53967.txt`
- Las Cases Vol II EN : `https://www.gutenberg.org/cache/epub/53968/pg53968.txt`
- Las Cases Vol III EN : `https://www.gutenberg.org/cache/epub/53969/pg53969.txt`
- Las Cases Vol IV EN : `https://www.gutenberg.org/cache/epub/53970/pg53970.txt`

### Bourrienne (secrétaire intime de Napoléon)

| Fichier | Langue | Taille | Source | Contenu |
|---------|--------|--------|--------|---------|
| `bourrienne_memoirs_napoleon_EN.txt` | EN | ~720 KB | Gutenberg #3567 | Mémoires complets de Bourrienne (EN) |
| `bourrienne_constant_memoirs_napoleon_EN.txt` | EN | ~5337 KB | Gutenberg #3740 | Collection complète : Bourrienne + Constant (valet) + Cour de St-Cloud |

**URLs de téléchargement direct :**
- Bourrienne seul EN : `https://www.gutenberg.org/cache/epub/3567/pg3567.txt`
- Collection Bourrienne+Constant EN : `https://www.gutenberg.org/cache/epub/3740/pg3740.txt`

### Journal de Sainte-Hélène — Gourgaud (aide de camp, témoin privilégié)

| Fichier | Langue | Taille | Source | Contenu |
|---------|--------|--------|--------|---------|
| `gourgaud_journal_sainte_helene_tome1_fr.txt` | FR | ~890 KB | Archive.org `saintehlnejo00gouruoft` | Journal de Sainte-Hélène Tome 1 — FR, OCR Univ. of Toronto |
| `gourgaud_journal_sainte_helene_tome2_fr.txt` | FR | ~1038 KB | Archive.org `saintehlnejo01gouruoft` | Journal de Sainte-Hélène Tome 2 — FR, OCR |

**URLs de téléchargement direct :**
- Gourgaud Tome 1 : `https://archive.org/download/saintehlnejo00gouruoft/saintehlnejo00gouruoft_djvu.txt`
- Gourgaud Tome 2 : `https://archive.org/download/saintehlnejo01gouruoft/saintehlnejo01gouruoft_djvu.txt`

### Mémoires pour servir à l'histoire de France — Méneval (secrétaire particulier)

| Fichier | Langue | Taille | Source | Contenu |
|---------|--------|--------|--------|---------|
| `meneval_memoires_napoleon_tome1_fr.txt` | FR | ~911 KB | Archive.org `mmoirespourser01mnuoft` | Mémoires Tome 1 — FR, OCR Univ. of Toronto |
| `meneval_memoires_napoleon_tome2_fr.txt` | FR | ~1030 KB | Archive.org `mmoirespourser02mnuoft` | Mémoires Tome 2 — FR, OCR |
| `meneval_memoires_napoleon_tome3_fr.txt` | FR | ~1166 KB | Archive.org `mmoirespourser03mnuoft` | Mémoires Tome 3 — FR, OCR |

**URLs de téléchargement direct :**
- Méneval Tome 1 : `https://archive.org/download/mmoirespourser01mnuoft/mmoirespourser01mnuoft_djvu.txt`
- Méneval Tome 2 : `https://archive.org/download/mmoirespourser02mnuoft/mmoirespourser02mnuoft_djvu.txt`
- Méneval Tome 3 : `https://archive.org/download/mmoirespourser03mnuoft/mmoirespourser03mnuoft_djvu.txt`

### Mémorial de Sainte-Hélène — Wikisource édition 1842 (texte propre)

| Fichier | Langue | Taille | Source | Contenu |
|---------|--------|--------|--------|---------|
| `las_cases_memorial_wikisource_fr.txt` | FR | ~3858 KB | Wikisource FR (édition Bourdin, 1842) | Mémorial complet — 40 chapitres + Préambule, texte propre (OCR corrigé par wikisource) |

**Source :** `https://fr.wikisource.org/wiki/Mémorial_de_Sainte-Hélène_(1842)`
Récupéré chapitre par chapitre via l'API Wikimedia (action=parse). Texte de qualité supérieure aux versions Archive.org.

---

## CATÉGORIE 3 — À enrichir (biographies, analyses)

Sources recommandées :
- Gallica BNF : `https://gallica.bnf.fr` → rechercher "Napoléon" + filtre "texte"
- Wikisource FR : `https://fr.wikisource.org/wiki/Portail:Napoléon_Bonaparte`
- Textes potentiels à ajouter :
  - Mémoires de Marmont (maréchal) → Gallica BNF
  - Mémoires de Constant en français → Gallica BNF
  - Proclamations militaires (Armée d'Italie, Grande Armée) → Wikisource
  - Correspondance officielle (décrets, notes) → Gallica

---

## Notes techniques

- Tous les textes sont en domaine public
- Format : texte brut UTF-8
- **Attention OCR** : les fichiers `las_cases_memorial_tome*_fr.txt` viennent d'OCR de livres scannés (1823) — des erreurs de caractères sont possibles, à nettoyer avant ingestion RAG
- Préprocessing : retirer les headers/footers Gutenberg avant ingestion RAG
- Les fichiers EN peuvent être utilisés en complément des sources FR pour le contexte
