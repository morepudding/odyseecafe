"""
webapp.py — Dashboard OdyséeCafé

Sidebar personnages + tabs Thread / Chat pour chaque IA active.

Usage : python src/webapp.py  →  http://localhost:5000
"""

import sys
import os
import json
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request, session, Response
from dotenv import load_dotenv
import secrets

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
sys.path.insert(0, str(Path(__file__).parent))

from editorial_db         import list_editorial_themes
from config               import env_value

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

DATA_DIR = Path(__file__).parent.parent / "data"
CURRENT_TOPIC_PATH = DATA_DIR / "current_topic.json"
APP_VERSION = (
    os.getenv("VERCEL_GIT_COMMIT_SHA")
    or os.getenv("VERCEL_GIT_COMMIT_REF")
    or "local"
)[:12]

_thread_state = {
    "question": None,
    "tweets": [],
    "sources": [],
    "mode": "balanced",
    "dossier": "",
    "angle": "",
    "character": "napoleon",
}

DOSSIER_PLACEHOLDER = """# Dossier editorial

## Sujet
- Question :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Origine :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Date de collecte :
  Pertinence au sujet : /5
  Potentiel buzz : /5

## Resume factuel court
En 5 a 8 lignes : ce qui s'est passe, ou, quand, qui est concerne, pourquoi c'est polemique.
- Resume :
  Pertinence au sujet : /5
  Potentiel buzz : /5

## 1. Faits chauds
- Date / lieu :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Declencheur :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Dernier etat connu :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Ce qui est confirme :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Ce qui reste incertain :
  Pertinence au sujet : /5
  Potentiel buzz : /5

## 2. Precedents historiques
- Cas comparable 1 :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Cas comparable 2 :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Ancienne promesse / ancien scandale / ancienne reforme :
  Pertinence au sujet : /5
  Potentiel buzz : /5

## 3. Dispositifs et institutions en place
- Institutions responsables :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Procedures existantes :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Controles prevus :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Failles possibles :
  Pertinence au sujet : /5
  Potentiel buzz : /5

## 4. Lois, reglements, decisions publiques
- Texte applicable :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Decision recente :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Rapport / enquete / commission :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Ce que le droit permet deja :
  Pertinence au sujet : /5
  Potentiel buzz : /5

## 5. Declarations politiques ou polemiques
- Gouvernement :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Opposition :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Experts / syndicats / associations :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Contradictions reperees :
  Pertinence au sujet : /5
  Potentiel buzz : /5

## 6. Comparaisons mediatiques
- Traitement mediatique dominant :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Differences selon les camps :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Deux poids deux mesures possible :
  Pertinence au sujet : /5
  Potentiel buzz : /5

## 7. Contre-exemples
- Cas similaire mieux gere :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Politique qui a fonctionne :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Element qui nuance l'accusation principale :
  Pertinence au sujet : /5
  Potentiel buzz : /5

## 8. Acteurs impliques
- Responsables directs :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Institutions :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Victimes / publics concernes :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Acteurs silencieux :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Qui gagne / qui perd politiquement :
  Pertinence au sujet : /5
  Potentiel buzz : /5

## 9. Chiffres simples et bilans
- Nombre de personnes concernees :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Couts / budgets :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Evolution dans le temps :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Ordre de grandeur utile :
  Pertinence au sujet : /5
  Potentiel buzz : /5

## Sources
- [S1] Titre - media/institution - URL - date
  Pertinence au sujet : /5
  Potentiel buzz : /5
- [S2] Titre - media/institution - URL - date
  Pertinence au sujet : /5
  Potentiel buzz : /5
- [S3] Titre - media/institution - URL - date
  Pertinence au sujet : /5
  Potentiel buzz : /5

## Points de vigilance
- Ne pas affirmer :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Faits a verifier :
  Pertinence au sujet : /5
  Potentiel buzz : /5
- Risque de diffamation / accusation trop directe :
  Pertinence au sujet : /5
  Potentiel buzz : /5"""

CHARACTERS = [
    {"id": "napoleon",      "name": "Napoléon Bonaparte", "emoji": "⚔️",  "active": True,  "era": "1769 – 1821"},
    {"id": "jeanne",        "name": "Jeanne d'Arc",       "emoji": "🛡️", "active": True,  "era": "1412 – 1431"},
    {"id": "antoinette",    "name": "Marie-Antoinette",   "emoji": "👑",  "active": False, "era": "1755 – 1793"},
    {"id": "voltaire",      "name": "Voltaire",           "emoji": "✒️",  "active": False, "era": "1694 – 1778"},
    {"id": "robespierre",   "name": "Robespierre",        "emoji": "🗡️", "active": False, "era": "1758 – 1794"},
]

THREAD_FALLBACK_PROMPT = """Tu es Napoléon Bonaparte. Tu t'exprimes à la première personne, avec autorité et conviction.
Tu écris un thread Twitter de 5 tweets numérotés sur la question posée.

Structure :
1/ Accroche percutante
2/ Parallèle historique ou militaire
3/ Vision politique
4/ Critique de ceux qui se trompent
5/ Conclusion mémorable

Contraintes :
- Commence chaque tweet par "1/" "2/" "3/" "4/" "5/"
- Chaque tweet doit rester sous 280 caractères
- Français uniquement
- Ne dis jamais que tu es une IA
- Retourne uniquement les 5 tweets."""

HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta name="theme-color" content="#080f1a">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="OdyséeCafé">
  <link rel="manifest" href="/manifest.webmanifest">
  <title>OdyséeCafé</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #080f1a; color: #e2e8f0;
      min-height: 100vh; display: flex;
      -webkit-font-smoothing: antialiased;
    }

    /* ── SIDEBAR ── */
    .sidebar {
      width: 220px; min-height: 100vh; flex-shrink: 0;
      background: #0d1829; border-right: 1px solid #1e2d45;
      display: flex; flex-direction: column;
      padding: 1.25rem .75rem;
      position: sticky; top: 0; height: 100vh; overflow-y: auto;
    }
    .sidebar-logo {
      font-size: 1.1rem; font-weight: 800; color: #f59e0b;
      padding: .25rem .5rem .75rem; letter-spacing: .02em;
      border-bottom: 1px solid #1e2d45; margin-bottom: 1rem;
    }
    .sidebar-logo span { color: #64748b; font-weight: 400; font-size: .75rem; display: block; }
    .sidebar-link {
      display: block; color: #cbd5e1; text-decoration: none;
      padding: .55rem .6rem; border-radius: 8px; font-size: .82rem;
      font-weight: 650; margin-bottom: .75rem; background: #14233a;
      border: 1px solid #1e2d45;
    }
    .sidebar-link:hover { background: #1e2d45; }
    .section-label {
      font-size: .65rem; font-weight: 700; letter-spacing: .12em;
      text-transform: uppercase; color: #475569; padding: .4rem .5rem .3rem;
    }
    .char-item {
      display: flex; align-items: center; gap: .6rem;
      padding: .55rem .6rem; border-radius: 8px; cursor: pointer;
      transition: background .15s; margin-bottom: 2px;
    }
    .char-item:hover { background: #1e2d45; }
    .char-item.active { background: #1e3a5f; }
    .char-item.locked { opacity: .45; cursor: default; }
    .char-item.locked:hover { background: transparent; }
    .char-emoji { font-size: 1.1rem; width: 24px; text-align: center; flex-shrink: 0; }
    .char-info { flex: 1; min-width: 0; }
    .char-name { font-size: .82rem; font-weight: 600; white-space: nowrap;
                 overflow: hidden; text-overflow: ellipsis; }
    .char-era  { font-size: .68rem; color: #64748b; }
    .char-badge {
      font-size: .6rem; padding: .1rem .35rem; border-radius: 99px;
      font-weight: 700; flex-shrink: 0;
    }
    .badge-live { background: #14532d; color: #86efac; }
    .badge-soon { background: #1e2d45; color: #475569; }

    /* ── MAIN ── */
    .main {
      flex: 1; padding: 2rem; display: flex; flex-direction: column; gap: 1.5rem;
      max-width: 760px;
    }

    /* character header */
    .char-header {
      display: flex; align-items: center; gap: 1rem;
    }
    .char-avatar {
      width: 52px; height: 52px; border-radius: 50%;
      background: linear-gradient(135deg,#f59e0b,#b45309);
      display: flex; align-items: center; justify-content: center;
      font-size: 1.6rem; flex-shrink: 0;
    }
    .char-header h1 { font-size: 1.3rem; font-weight: 800; }
    .char-header .meta { font-size: .8rem; color: #64748b; margin-top: 2px; }

    /* coming soon panel */
    .coming-soon {
      background: #0d1829; border: 1px dashed #1e2d45; border-radius: 14px;
      padding: 3rem 2rem; text-align: center; color: #475569;
      display: none;
    }
    .coming-soon.visible { display: block; }
    .coming-soon h2 { font-size: 1rem; margin-bottom: .5rem; color: #64748b; }

    /* ── TABS ── */
    .tabs { display: flex; gap: 0; border-bottom: 1px solid #1e2d45; }
    .tab-btn {
      padding: .6rem 1.1rem; font-size: .85rem; font-weight: 600;
      background: none; border: none; color: #64748b; cursor: pointer;
      border-bottom: 2px solid transparent; margin-bottom: -1px;
      transition: color .15s;
    }
    .tab-btn:hover { color: #94a3b8; }
    .tab-btn.active { color: #f1f5f9; border-bottom-color: #f59e0b; }
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }

    /* ── THREAD TAB ── */
    .label {
      font-size: .68rem; font-weight: 700; letter-spacing: .1em;
      text-transform: uppercase; color: #64748b; margin-bottom: .5rem;
    }
    .question-box {
      background: #0d1829; border: 1px solid #1e2d45; border-radius: 10px;
      padding: .9rem 1rem; margin-bottom: 1.5rem;
      font-size: .95rem; line-height: 1.55; color: #f1f5f9;
    }
    .thread { display: flex; flex-direction: column; margin-bottom: 1.5rem; }
    .tweet-row { display: flex; gap: .75rem; align-items: stretch; }
    .thread-line {
      display: flex; flex-direction: column; align-items: center;
      width: 28px; flex-shrink: 0;
    }
    .dot {
      width: 9px; height: 9px; border-radius: 50%;
      background: #f59e0b; margin-top: .9rem; flex-shrink: 0;
    }
    .vline { width: 2px; background: #1e2d45; flex: 1; margin-top: 3px; }
    .tweet-row:last-child .vline { display: none; }
    .tweet-wrap { flex: 1; padding-bottom: .9rem; }
    .tweet-num { font-size: .68rem; color: #475569; margin-bottom: .25rem; }
    .tweet-box {
      background: #0d1829; border: 1px solid #1e3a5f; border-radius: 10px;
      padding: .8rem 1rem; font-size: .9rem; line-height: 1.6; color: #e2e8f0;
      white-space: pre-wrap; outline: none; min-height: 3.5rem;
    }
    .tweet-box:focus { border-color: #3b82f6; }
    .tweet-footer {
      display: flex; justify-content: space-between; align-items: center;
      margin-top: .3rem;
    }
    .char-count { font-size: .7rem; color: #475569; }
    .char-count.warn { color: #f59e0b; }
    .char-count.over { color: #ef4444; }
    .btn-copy-one {
      background: none; border: 1px solid #1e2d45; color: #64748b;
      border-radius: 6px; padding: .2rem .6rem; font-size: .7rem;
      cursor: pointer; transition: all .15s;
    }
    .btn-copy-one:hover { background: #1e2d45; color: #e2e8f0; }
    .copied { color: #86efac !important; border-color: #14532d !important; }

    .actions { display: flex; gap: .75rem; flex-wrap: wrap; }
    button.act {
      padding: .6rem 1.1rem; border: none; border-radius: 8px;
      font-size: .88rem; font-weight: 600; cursor: pointer; transition: opacity .15s;
    }
    button.act:hover { opacity: .85; }
    button.act:disabled { opacity: .35; cursor: not-allowed; }
    .btn-regen { background: #1e2d45; color: #e2e8f0; }
    .btn-all   { background: #1d4ed8; color: white; flex: 1; }
    .btn-x     { background: #14532d; color: #86efac; }
    .btn-tone  { background: #312e81; color: #c7d2fe; }
    .btn-history { background: #4a2f14; color: #fed7aa; }

    .composer {
      display: grid; gap: .7rem; margin-bottom: 1.25rem;
      background: #0d1829; border: 1px solid #1e2d45; border-radius: 12px;
      padding: .9rem;
    }
    .composer textarea {
      width: 100%; min-height: 76px; resize: vertical;
      background: #080f1a; border: 1px solid #1e2d45; border-radius: 8px;
      color: #e2e8f0; padding: .7rem .85rem; font: inherit; line-height: 1.45;
      outline: none;
    }
    .composer textarea:focus { border-color: #3b82f6; }
    .composer-actions { display: flex; gap: .65rem; flex-wrap: wrap; }
    .field-label {
      font-size: .66rem; font-weight: 750; letter-spacing: .08em;
      text-transform: uppercase; color: #64748b; margin-bottom: .35rem;
    }
    .brief-grid { display: grid; gap: .7rem; }
    .brief-grid textarea { min-height: 110px; }
    #editorial-dossier { min-height: 190px; }
    #editorial-angle { min-height: 98px; }
    .theme-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: .55rem; margin: .35rem 0 1.25rem;
    }
    .theme-card {
      text-align: left; background: #0d1829; border: 1px solid #1e2d45;
      color: #cbd5e1; border-radius: 8px; padding: .65rem .75rem;
      min-height: 58px;
    }
    .theme-name { color: #f8fafc; font-size: .82rem; font-weight: 750; margin-bottom: .3rem; }
    .theme-desc { color: #94a3b8; font-size: .74rem; line-height: 1.4; }

    .sources-panel {
      margin-top: 1.25rem; background: #0d1829; border: 1px solid #1e2d45;
      border-radius: 12px; padding: .9rem;
    }
    .source-list { display: grid; gap: .65rem; }
    .source-card {
      border: 1px solid #1e2d45; border-radius: 9px; padding: .7rem;
      background: #08111f;
    }
    .source-title { color: #f8fafc; font-size: .78rem; font-weight: 750; margin-bottom: .25rem; }
    .source-meta { color: #64748b; font-size: .68rem; margin-bottom: .35rem; }
    .source-excerpt { color: #94a3b8; font-size: .76rem; line-height: 1.45; }

    /* ── CHAT TAB ── */
    .chat-window {
      background: #0d1829; border: 1px solid #1e2d45; border-radius: 12px;
      display: flex; flex-direction: column; height: 460px; overflow: hidden;
    }
    .chat-messages {
      flex: 1; overflow-y: auto; padding: 1rem; display: flex;
      flex-direction: column; gap: .75rem;
    }
    .chat-messages::-webkit-scrollbar { width: 4px; }
    .chat-messages::-webkit-scrollbar-track { background: transparent; }
    .chat-messages::-webkit-scrollbar-thumb { background: #1e2d45; border-radius: 2px; }
    .msg { display: flex; gap: .6rem; align-items: flex-start; }
    .msg.user { flex-direction: row-reverse; }
    .msg-avatar {
      width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
      display: flex; align-items: center; justify-content: center; font-size: .9rem;
    }
    .msg.napoleon .msg-avatar { background: linear-gradient(135deg,#f59e0b,#b45309); }
    .msg.jeanne   .msg-avatar { background: linear-gradient(135deg,#6366f1,#3730a3); }
    .msg.user     .msg-avatar { background: #1e2d45; }
    .msg-bubble {
      max-width: 80%; padding: .65rem .9rem; border-radius: 12px;
      font-size: .88rem; line-height: 1.55; white-space: pre-wrap;
    }
    .msg.napoleon .msg-bubble { background: #0f2340; color: #e2e8f0; border: 1px solid #1e3a5f; }
    .msg.user     .msg-bubble { background: #1d4ed8; color: white; }
    .msg-name { font-size: .65rem; color: #475569; margin-bottom: .2rem; }
    .chat-input-row {
      border-top: 1px solid #1e2d45; padding: .75rem; display: flex; gap: .6rem;
    }
    .chat-input {
      flex: 1; background: #080f1a; border: 1px solid #1e2d45; color: #e2e8f0;
      border-radius: 8px; padding: .55rem .85rem; font-size: .88rem; outline: none;
      resize: none; height: 42px; font-family: inherit;
    }
    .chat-input:focus { border-color: #3b82f6; }
    .btn-send {
      background: #f59e0b; color: #080f1a; border: none; border-radius: 8px;
      width: 42px; height: 42px; font-size: 1rem; cursor: pointer;
      transition: opacity .15s; flex-shrink: 0;
    }
    .btn-send:hover { opacity: .85; }
    .btn-send:disabled { opacity: .35; cursor: not-allowed; }
    .typing-dot {
      display: inline-block; width: 6px; height: 6px; border-radius: 50%;
      background: #64748b; margin: 0 2px;
      animation: blink 1.2s infinite;
    }
    .typing-dot:nth-child(2) { animation-delay: .2s; }
    .typing-dot:nth-child(3) { animation-delay: .4s; }
    @keyframes blink { 0%,80%,100%{opacity:.2} 40%{opacity:1} }

    /* spinner */
    .spinner {
      display: inline-block; width: 13px; height: 13px;
      border: 2px solid rgba(255,255,255,.3); border-top-color: white;
      border-radius: 50%; animation: spin .6s linear infinite;
      vertical-align: middle; margin-right: 5px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* stats bar */
    .stats-bar {
      display: flex; gap: 1rem; flex-wrap: wrap;
    }
    .stat-chip {
      background: #0d1829; border: 1px solid #1e2d45; border-radius: 8px;
      padding: .45rem .85rem; font-size: .78rem; color: #94a3b8;
    }
    .stat-chip strong { color: #f1f5f9; }

    @media (max-width: 760px) {
      body {
        display: block;
        min-height: 100svh;
        padding: env(safe-area-inset-top) 0 env(safe-area-inset-bottom);
        overflow-x: hidden;
      }

      .sidebar {
        width: 100%;
        min-height: 0;
        height: auto;
        position: sticky;
        top: 0;
        z-index: 20;
        padding: .75rem .75rem .65rem;
        border-right: 0;
        border-bottom: 1px solid #1e2d45;
      }

      .sidebar-logo {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: .8rem;
        padding: 0 0 .65rem;
        margin-bottom: .55rem;
        font-size: 1rem;
      }

      .sidebar-logo span {
        display: inline;
        text-align: right;
      }

      .section-label {
        display: none;
      }

      .sidebar .char-item {
        display: inline-flex;
        width: max-content;
        min-height: 48px;
        margin: 0 .4rem 0 0;
        vertical-align: top;
      }

      .sidebar {
        white-space: nowrap;
        overflow-x: auto;
        overflow-y: hidden;
        scrollbar-width: none;
      }

      .sidebar::-webkit-scrollbar {
        display: none;
      }

      .char-info {
        max-width: 132px;
      }

      .char-era,
      .char-badge {
        display: none;
      }

      .main {
        width: 100%;
        max-width: none;
        padding: 1rem .85rem 1.4rem;
        gap: 1rem;
      }

      .char-header {
        align-items: flex-start;
      }

      .char-avatar {
        width: 46px;
        height: 46px;
      }

      .char-header h1 {
        font-size: 1.12rem;
      }

      .stats-bar {
        gap: .5rem;
        overflow-x: auto;
        flex-wrap: nowrap;
        padding-bottom: .15rem;
        scrollbar-width: none;
      }

      .stats-bar::-webkit-scrollbar {
        display: none;
      }

      .stat-chip {
        flex: 0 0 auto;
        padding: .42rem .65rem;
      }

      .tabs {
        gap: .35rem;
        overflow-x: auto;
        border-bottom: 0;
        padding-bottom: .15rem;
        scrollbar-width: none;
      }

      .tabs::-webkit-scrollbar {
        display: none;
      }

      .tab-btn {
        flex: 0 0 auto;
        min-height: 44px;
        padding: .55rem .78rem;
        border: 1px solid #1e2d45;
        border-radius: 999px;
        background: #0d1829;
        margin-bottom: 0;
        white-space: nowrap;
      }

      .tab-btn.active {
        color: #080f1a;
        background: #f59e0b;
        border-color: #f59e0b;
      }

      .composer,
      .question-box,
      .tweet-box,
      .sources-panel,
      .chat-window {
        border-radius: 14px;
      }

      .composer {
        padding: .75rem;
      }

      .composer textarea {
        font-size: 16px;
      }

      .composer-actions,
      .actions {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: .55rem;
      }

      button.act {
        min-height: 46px;
        padding: .55rem .75rem;
      }

      .theme-grid {
        grid-template-columns: 1fr;
        gap: .5rem;
      }

      .theme-card {
        min-height: 0;
      }

      .tweet-row {
        gap: .45rem;
      }

      .thread-line {
        width: 18px;
      }

      .tweet-box {
        padding: .75rem .82rem;
        font-size: .88rem;
      }

      .tweet-footer {
        min-height: 36px;
      }

      .btn-copy-one {
        min-height: 34px;
        padding: .25rem .75rem;
      }

      #editorial-dossier {
        min-height: 170px;
      }

      .chat-window {
        height: calc(100svh - 255px);
        min-height: 430px;
      }

      .msg-bubble {
        max-width: 86vw;
      }

      .chat-input-row {
        padding: .65rem;
      }

      .chat-input {
        height: 44px;
        font-size: 16px;
      }

      .btn-send {
        width: 44px;
        height: 44px;
      }
    }
  </style>
</head>
<body>

<!-- SIDEBAR -->
<nav class="sidebar">
  <div class="sidebar-logo">OdyséeCafé<span>Les immortels tweetent.</span></div>
  <a class="sidebar-link" href="/dossier">Sujet du jour</a>
  <div class="section-label">Personnages</div>
  {% for c in characters %}
  <div class="char-item {% if c.active %}{% if c.id == active_id %}active{% endif %}{% else %}locked{% endif %}"
       {% if c.active %}onclick="selectChar('{{ c.id }}')"{% endif %}>
    <span class="char-emoji">{{ c.emoji }}</span>
    <span class="char-info">
      <span class="char-name">{{ c.name }}</span>
      <span class="char-era">{{ c.era }}</span>
    </span>
    <span class="char-badge {% if c.active %}badge-live{% else %}badge-soon{% endif %}">
      {% if c.active %}live{% else %}soon{% endif %}
    </span>
  </div>
  {% endfor %}
</nav>

<!-- MAIN -->
<main class="main">

  <!-- character header -->
  <div class="char-header" id="char-header">
    <div class="char-avatar">⚔️</div>
    <div>
      <h1>Napoléon Bonaparte</h1>
      <div class="meta">1769 – 1821 · @OdyseeCafe · actif</div>
    </div>
  </div>

  <!-- coming soon panel (hidden by default) -->
  <div class="coming-soon" id="coming-soon">
    <h2>Bientôt au café…</h2>
    <p>Ce personnage est en cours de construction.<br>Le corpus sera ingéré prochainement.</p>
  </div>

  <!-- stats -->
  <div class="stats-bar" id="stats-bar">
    <div class="stat-chip">Corpus : <strong>{{ chunk_count }} chunks</strong></div>
    <div class="stat-chip">Modèle : <strong>{{ model }}</strong></div>
    <div class="stat-chip">Embeddings : <strong>nvidia/llama-nemotron</strong></div>
  </div>

  <!-- TABS -->
  <div id="active-panel">
    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab('thread', this)">🧵 Générateur de threads</button>
      <button class="tab-btn"        onclick="switchTab('chat',   this)">💬 Chat secondaire</button>
    </div>

    <!-- THREAD TAB -->
    <div class="tab-panel active" id="tab-thread" style="padding-top:1.25rem">
      <div class="label">Brief éditorial</div>
      <div class="composer">
        <div>
          <div class="field-label">Sujet polémique</div>
          <textarea id="manual-question" placeholder="Ex : Faut-il rétablir le service militaire obligatoire ?">{{ question }}</textarea>
        </div>

        <div class="brief-grid">
          <div>
            <div class="field-label">Dossier</div>
            <textarea id="editorial-dossier" placeholder="{{ dossier_placeholder }}">{{ dossier }}</textarea>
          </div>
          <div>
            <div class="field-label">Angle</div>
            <textarea id="editorial-angle" placeholder="Émotion à provoquer, question à laisser au lecteur, tension morale ou politique à faire sentir.">{{ angle }}</textarea>
          </div>
        </div>

        <div class="composer-actions">
          <button class="act btn-regen" onclick="loadTopic(this)">Charger le brief</button>
          <button class="act btn-all" onclick="doRegen('balanced', this)">Générer ce brief</button>
          <button class="act btn-tone" onclick="doRegen('sharp', this)">Plus tranchant</button>
          <button class="act btn-history" onclick="doRegen('historical', this)">Plus historique</button>
        </div>
      </div>

      <div class="label">Thèmes éditoriaux validés</div>
      <div class="theme-grid">
        {% for theme in editorial_themes %}
        <div class="theme-card">
          <div class="theme-name">{{ theme.name }}</div>
          <div class="theme-desc">{{ theme.description }}</div>
        </div>
        {% endfor %}
      </div>

      <div class="label">Question traitée</div>
      <div class="question-box" id="question">{{ question }}</div>

      <div class="label">Thread (modifiable avant copie)</div>
      <div class="thread" id="thread">
        {% for i, tweet in tweets %}
        <div class="tweet-row" id="row-{{ i }}">
          <div class="thread-line">
            <div class="dot"></div><div class="vline"></div>
          </div>
          <div class="tweet-wrap">
            <div class="tweet-num">{{ i }}/5</div>
            <div class="tweet-box" contenteditable="true" id="tweet-{{ i }}"
                 oninput="updateCount({{ i }})">{{ tweet }}</div>
            <div class="tweet-footer">
              <span class="char-count" id="cc-{{ i }}">{{ tweet|length }}/280</span>
              <button class="btn-copy-one" onclick="copySingle({{ i }})">Copier</button>
            </div>
          </div>
        </div>
        {% endfor %}
      </div>

      <div class="actions">
        <button class="act btn-regen" onclick="doRegen('balanced', this)">🔄 Regénérer</button>
        <button class="act btn-all"   onclick="copyAll()">📋 Copier tout</button>
        <button class="act btn-x"     onclick="window.open('https://x.com/compose/post','_blank')">🐦 Ouvrir X</button>
      </div>

      <div class="sources-panel">
        <div class="label">Sources RAG utilisées</div>
        <div class="source-list" id="sources">
          {% for source in sources %}
          <div class="source-card">
            <div class="source-title">{{ source.source or source.title or source.url or "Source" }}</div>
            <div class="source-meta">
              {% if source.distance is defined %}distance {{ source.distance }}{% else %}{{ source.url or "" }}{% endif %}
            </div>
            <div class="source-excerpt">{{ source.excerpt or source.published or "" }}</div>
          </div>
          {% else %}
          <div class="source-card">
            <div class="source-title">Aucune source disponible</div>
            <div class="source-excerpt">La collection ChromaDB est vide. Lance l'ingestion du corpus pour réactiver le RAG.</div>
          </div>
          {% endfor %}
        </div>
      </div>
    </div>

    <!-- CHAT TAB -->
    <div class="tab-panel" id="tab-chat" style="padding-top:1.25rem">
      <div class="chat-window">
        <div class="chat-messages" id="chat-messages">
        </div>
        <div class="chat-input-row">
          <textarea class="chat-input" id="chat-input" placeholder="Posez votre question…"
                    onkeydown="chatKeydown(event)" rows="1"></textarea>
          <button class="btn-send" id="btn-send" onclick="sendChat()">➤</button>
        </div>
      </div>
    </div>
  </div>

</main>

<script>
  // ── CHARACTER DATA (mirrors Python) ──
  const CHARS = {{ characters_json | safe }};

  // Personnage actif courant (Napoleon par défaut)
  let currentChar = CHARS.find(x => x.id === 'napoleon') || CHARS[0];

  const CHAR_GREETINGS = {
    napoleon: 'Que voulez-vous savoir ? Je suis là.',
    jeanne:   'En nom de Dieu, posez votre question. Je vous répondrai.',
  };

  function selectChar(id) {
    const c = CHARS.find(x => x.id === id);
    if (!c || !c.active) return;

    currentChar = c;

    // Update sidebar highlight
    document.querySelectorAll('.char-item').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');

    // Update header
    document.querySelector('#char-header .char-avatar').textContent = c.emoji;
    document.querySelector('#char-header h1').textContent = c.name;
    document.querySelector('#char-header .meta').textContent =
      c.era + ' · @OdyseeCafe · actif';

    document.getElementById('coming-soon').classList.remove('visible');
    document.getElementById('active-panel').style.display = '';
    document.getElementById('stats-bar').style.display = '';

    // Reset chat window for the new character
    resetChat();
  }

  function resetChat() {
    const box = document.getElementById('chat-messages');
    box.innerHTML = '';
    const greeting = CHAR_GREETINGS[currentChar.id] || 'Bonjour.';
    appendMsg('ai', greeting);
  }

  // ── TABS ──
  function switchTab(name, btn) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + name).classList.add('active');
  }

  // ── THREAD ──
  function updateCount(i) {
    const box = document.getElementById('tweet-' + i);
    const cc  = document.getElementById('cc-' + i);
    const n   = box.innerText.length;
    cc.textContent = n + '/280';
    cc.className = 'char-count' + (n > 280 ? ' over' : n > 260 ? ' warn' : '');
  }
  for (let i = 1; i <= 5; i++) updateCount(i);

  function copySingle(i) {
    navigator.clipboard.writeText(document.getElementById('tweet-' + i).innerText).then(() => {
      const btn = document.querySelector(`#row-${i} .btn-copy-one`);
      const orig = btn.textContent;
      btn.textContent = '✓ Copié'; btn.classList.add('copied');
      setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 1800);
    });
  }

  function copyAll() {
    const parts = [];
    for (let i = 1; i <= 5; i++) parts.push(document.getElementById('tweet-' + i).innerText);
    navigator.clipboard.writeText(parts.join('\\n\\n')).then(() => {
      const btn = document.querySelector('.btn-all');
      const orig = btn.innerHTML;
      btn.innerHTML = '✓ Thread copié !';
      setTimeout(() => btn.innerHTML = orig, 2000);
    });
  }

  function renderSources(sources) {
    const root = document.getElementById('sources');
    root.innerHTML = '';
    (sources || []).forEach((s) => {
      const card = document.createElement('div');
      card.className = 'source-card';
      const title = s.source || s.title || s.url || 'Source';
      const meta = s.distance !== undefined ? `distance ${s.distance}` : (s.url || '');
      const excerpt = s.excerpt || s.published || '';
      card.innerHTML = `
        <div class="source-title">${String(title).replace(/</g,'&lt;')}</div>
        <div class="source-meta">${String(meta).replace(/</g,'&lt;')}</div>
        <div class="source-excerpt">${String(excerpt).replace(/</g,'&lt;')}</div>`;
      root.appendChild(card);
    });
    if (!sources || sources.length === 0) {
      const card = document.createElement('div');
      card.className = 'source-card';
      card.innerHTML = `
        <div class="source-title">Aucune source disponible</div>
        <div class="source-excerpt">La collection ChromaDB est vide. Lance l'ingestion du corpus pour réactiver le RAG.</div>`;
      root.appendChild(card);
    }
  }

  function applyBrief(d) {
    document.getElementById('question').textContent = d.question || '';
    document.getElementById('manual-question').value = d.question || '';
    document.getElementById('editorial-dossier').value = d.dossier || '';
    document.getElementById('editorial-angle').value = d.angle || '';
    renderSources(d.sources || []);
  }

  function loadTopic(btn = null) {
    btn = btn || document.querySelector('.btn-regen');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Chargement…';
    fetch('/api/topic', {cache: 'no-store'})
      .then(r => r.json())
      .then(d => {
        if (d.ok) {
          applyBrief(d);
        } else {
          alert('Erreur : ' + d.error);
        }
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalLabel || btn.textContent;
      })
      .catch(() => {
        alert('Erreur : impossible de charger le brief.');
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalLabel || btn.textContent;
      });
  }

  function doRegen(mode = 'balanced', btn = null) {
    btn = btn || document.querySelector('.btn-regen');
    const manualQuestion = document.getElementById('manual-question').value.trim();
    const dossier = document.getElementById('editorial-dossier').value.trim();
    const angle = document.getElementById('editorial-angle').value.trim();
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Génération…';
    fetch('/api/thread', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        question: manualQuestion,
        dossier,
        angle,
        character: currentChar.id,
        mode,
      }),
    })
      .then(r => r.json())
      .then(d => {
        if (d.ok) {
          applyBrief(d);
          d.tweets.forEach((t, idx) => {
            const i = idx + 1;
            document.getElementById('tweet-' + i).innerText = t;
            updateCount(i);
          });
        } else { alert('Erreur : ' + d.error); }
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalLabel || btn.textContent;
      })
      .catch(() => {
        alert('Erreur : impossible de contacter le serveur de génération.');
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalLabel || btn.textContent;
      });
  }

  document.querySelectorAll('.composer .act, .actions .btn-regen').forEach((btn) => {
    btn.dataset.originalLabel = btn.innerHTML;
  });

  // ── CHAT ──
  const chatHistory = [];

  function appendMsg(role, text) {
    const box = document.getElementById('chat-messages');
    const div = document.createElement('div');
    const isAI = role !== 'user';
    div.className = 'msg ' + (isAI ? currentChar.id : 'user');
    const avatarText = isAI ? currentChar.emoji : '🧑';
    const nameText   = isAI ? currentChar.name  : 'Vous';
    div.innerHTML = `
      <div class="msg-avatar">${avatarText}</div>
      <div>
        <div class="msg-name">${nameText}</div>
        <div class="msg-bubble">${text.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>
      </div>`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    return div;
  }

  function appendTyping() {
    const box = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'msg ' + currentChar.id; div.id = 'typing-indicator';
    div.innerHTML = `
      <div class="msg-avatar">${currentChar.emoji}</div>
      <div><div class="msg-name">${currentChar.name}</div>
      <div class="msg-bubble">
        <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
      </div></div>`;
    box.appendChild(div); box.scrollTop = box.scrollHeight;
  }

  function removeTyping() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
  }

  function sendChat() {
    const input = document.getElementById('chat-input');
    const msg   = input.value.trim();
    if (!msg) return;
    input.value = '';

    appendMsg('user', msg);
    chatHistory.push({role:'user', content: msg});

    const btn = document.getElementById('btn-send');
    btn.disabled = true;
    appendTyping();

    fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: msg, character: currentChar.id}),
    })
    .then(r => r.json())
    .then(d => {
      removeTyping();
      if (d.ok) {
        appendMsg('napoleon', d.reply);
        chatHistory.push({role:'assistant', content: d.reply});
      } else {
        appendMsg('napoleon', '⚠️ Erreur : ' + d.error);
      }
      btn.disabled = false;
    })
    .catch(err => {
      removeTyping();
      appendMsg('napoleon', '⚠️ Impossible de contacter le serveur.');
      btn.disabled = false;
    });
  }

  function chatKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
  }
</script>
<script>
  if ('serviceWorker' in navigator) {
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (refreshing) return;
      refreshing = true;
      window.location.reload();
    });
    navigator.serviceWorker.register('/sw.js?v={{ app_version }}').then((registration) => {
      registration.update().catch(() => {});
      if (registration.waiting) {
        registration.waiting.postMessage({type: 'SKIP_WAITING'});
      }
      registration.addEventListener('updatefound', () => {
        const worker = registration.installing;
        if (!worker) return;
        worker.addEventListener('statechange', () => {
          if (worker.state === 'installed' && navigator.serviceWorker.controller) {
            worker.postMessage({type: 'SKIP_WAITING'});
          }
        });
      });
    }).catch(() => {});
  }
  // Initialiser le chat avec le message de bienvenue du personnage par défaut
  document.addEventListener('DOMContentLoaded', () => resetChat());
</script>
</body>
</html>
"""


DOSSIER_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>OdyséeCafé — Sujet du jour</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #080f1a; color: #e2e8f0; min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }
    .page {
      width: min(980px, calc(100% - 2rem)); margin: 0 auto;
      padding: 2rem 0 2.5rem; display: grid; gap: 1rem;
    }
    .topbar {
      display: flex; justify-content: space-between; align-items: center;
      gap: 1rem; padding-bottom: .75rem; border-bottom: 1px solid #1e2d45;
    }
    .brand { color: #f59e0b; font-size: 1rem; font-weight: 850; }
    .nav-link {
      color: #cbd5e1; text-decoration: none; border: 1px solid #1e2d45;
      border-radius: 8px; padding: .45rem .75rem; font-size: .82rem;
      background: #0d1829;
    }
    h1 { font-size: 1.35rem; line-height: 1.25; }
    .meta { color: #64748b; font-size: .78rem; margin-top: .25rem; }
    .panel {
      background: #0d1829; border: 1px solid #1e2d45;
      border-radius: 10px; padding: 1rem; display: grid; gap: .8rem;
    }
    .label {
      font-size: .68rem; font-weight: 750; letter-spacing: .1em;
      text-transform: uppercase; color: #64748b;
    }
    .question {
      color: #f8fafc; font-size: 1rem; line-height: 1.55;
      background: #08111f; border: 1px solid #1e2d45;
      border-radius: 8px; padding: .9rem;
    }
    .collect-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: .6rem;
    }
    .collect-card {
      background: #08111f; border: 1px solid #1e2d45;
      border-radius: 8px; padding: .75rem; color: #cbd5e1;
      font-size: .8rem; line-height: 1.45;
    }
    .collect-title { color: #f8fafc; font-weight: 800; margin-bottom: .25rem; }
    .collect-intent { color: #94a3b8; margin-top: .25rem; }
    textarea {
      width: 100%; resize: vertical; min-height: 210px;
      background: #08111f; border: 1px solid #1e2d45; border-radius: 8px;
      color: #e2e8f0; padding: .85rem; font: inherit; line-height: 1.5;
      outline: none;
    }
    textarea:focus { border-color: #3b82f6; }
    #angle { min-height: 120px; }
    .actions { display: flex; gap: .7rem; flex-wrap: wrap; }
    button, .button-link {
      border: 0; border-radius: 8px; padding: .65rem 1rem;
      font-size: .88rem; font-weight: 700; cursor: pointer;
      text-decoration: none; display: inline-flex; align-items: center;
      justify-content: center; min-height: 42px;
    }
    button:disabled { opacity: .45; cursor: not-allowed; }
    .primary { background: #1d4ed8; color: white; }
    .secondary { background: #1e2d45; color: #e2e8f0; }
    .success { background: #14532d; color: #86efac; }
    .status { color: #94a3b8; font-size: .82rem; min-height: 1.2rem; }
    .spinner {
      display: inline-block; width: 13px; height: 13px;
      border: 2px solid rgba(255,255,255,.3); border-top-color: white;
      border-radius: 50%; animation: spin .6s linear infinite;
      vertical-align: middle; margin-right: 6px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    @media (max-width: 720px) {
      .page { width: 100%; padding: 1rem .85rem 1.4rem; }
      .topbar { align-items: flex-start; }
      .actions { display: grid; grid-template-columns: 1fr; }
      textarea { font-size: 16px; }
    }
  </style>
</head>
<body>
  <main class="page">
    <div class="topbar">
      <div>
        <div class="brand">OdyséeCafé</div>
      <div class="meta">Collecte d'abord, écriture ensuite</div>
      </div>
      <a class="nav-link" href="/">Générateur</a>
    </div>

    <section class="panel">
      <div>
        <div class="label">Sujet du jour</div>
        <h1>{{ question }}</h1>
        <div class="meta">Origine : {{ origin }}</div>
      </div>
      <div class="question" id="question">{{ question }}</div>
    </section>

    <section class="panel">
      <div class="label">Matrice de collecte universelle</div>
      <div class="collect-grid">
        <div class="collect-card">
          <div class="collect-title">1. Faits chauds</div>
          Ce qui vient de se passer : date, lieu, déclencheur, premiers bilans.
          <div class="collect-intent">Intention : établir le socle factuel immédiat.</div>
        </div>
        <div class="collect-card">
          <div class="collect-title">2. Précédents historiques</div>
          Épisodes similaires, archives, répétitions, anciens scandales, vieilles promesses.
          <div class="collect-intent">Intention : voir si le fait est un accident ou un symptôme.</div>
        </div>
        <div class="collect-card">
          <div class="collect-title">3. Dispositifs, institutions ou mécanismes en place</div>
          Organisation concrète : services responsables, procédures, contrôles, moyens prévus.
          <div class="collect-intent">Intention : comprendre qui était censé agir et comment.</div>
        </div>
        <div class="collect-card">
          <div class="collect-title">4. Lois, règlements et décisions publiques</div>
          Textes applicables, arrêtés, rapports, décisions administratives ou judiciaires.
          <div class="collect-intent">Intention : savoir ce que le droit permet déjà.</div>
        </div>
        <div class="collect-card">
          <div class="collect-title">5. Déclarations politiques ou polémiques</div>
          Ministres, élus, syndicats, experts, éditorialistes, prises de position anciennes.
          <div class="collect-intent">Intention : trouver les contradictions et lignes de fracture.</div>
        </div>
        <div class="collect-card">
          <div class="collect-title">6. Comparaisons médiatiques</div>
          Traitement du même type de fait selon contexte, camp politique, groupe ou époque.
          <div class="collect-intent">Intention : tester le deux poids deux mesures.</div>
        </div>
        <div class="collect-card">
          <div class="collect-title">7. Contre-exemples</div>
          Cas similaires mieux gérés, événements calmes, politiques qui ont fonctionné.
          <div class="collect-intent">Intention : éviter le récit à sens unique.</div>
        </div>
        <div class="collect-card">
          <div class="collect-title">8. Acteurs impliqués</div>
          Institutions, groupes, associations, entreprises, responsables, opposants.
          <div class="collect-intent">Intention : identifier qui gagne, perd, parle ou se tait.</div>
        </div>
        <div class="collect-card">
          <div class="collect-title">9. Chiffres simples et bilans</div>
          Ordres de grandeur : personnes touchées, coûts, interpellations, budgets, évolution.
          <div class="collect-intent">Intention : donner une prise concrète au lecteur.</div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="label">Dossier</div>
      <textarea id="dossier" placeholder="{{ dossier_placeholder }}">{{ dossier }}</textarea>
    </section>

    <section class="panel">
      <div class="label">Angle</div>
      <textarea id="angle" placeholder="L'angle éditorial apparaîtra ici.">{{ angle }}</textarea>
      <div class="actions">
        <button class="secondary" id="save-btn" onclick="saveBrief(this)">Enregistrer le brief</button>
        <a class="button-link success" href="/">Ouvrir le générateur</a>
      </div>
      <div class="status" id="status"></div>
    </section>
  </main>

  <script>
    const topic = {
      question: {{ question_json | safe }},
      character: {{ character_json | safe }},
    };

    function status(text) {
      document.getElementById('status').textContent = text || '';
    }

    function setBusy(btn, text) {
      btn.disabled = true;
      btn.dataset.originalLabel = btn.dataset.originalLabel || btn.innerHTML;
      btn.innerHTML = '<span class="spinner"></span>' + text;
    }

    function clearBusy(btn) {
      btn.disabled = false;
      btn.innerHTML = btn.dataset.originalLabel || btn.textContent;
    }

    function saveBrief(btn) {
      setBusy(btn, 'Enregistrement...');
      fetch('/api/topic', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          question: topic.question,
          dossier: document.getElementById('dossier').value.trim(),
          angle: document.getElementById('angle').value.trim(),
          sources: [],
          character: topic.character,
          origin: 'dossier_page',
        }),
      })
      .then(r => r.json())
      .then(d => {
        if (!d.ok) throw new Error(d.error || 'Erreur inconnue');
        status('Brief enregistré.');
      })
      .catch(err => status('Erreur : ' + err.message))
      .finally(() => clearBusy(btn));
    }
  </script>
</body>
</html>
"""


# ── ROUTES ────────────────────────────────────────────────────────────────────

def _get_thread_state():
    if not _thread_state["question"]:
        current_topic = _load_current_topic()
        q = (current_topic or {}).get("question") or "Colle ici un sujet éditorial."
        _thread_state["question"] = q
        _thread_state["tweets"] = [""] * 5
        _thread_state["sources"] = (current_topic or {}).get("sources") or []
        _thread_state["dossier"] = (current_topic or {}).get("dossier") or ""
        _thread_state["angle"] = (current_topic or {}).get("angle") or ""
        _thread_state["character"] = (current_topic or {}).get("character") or "napoleon"
    return _thread_state


def _load_current_topic() -> dict | None:
    try:
        if not CURRENT_TOPIC_PATH.exists():
            return None
        data = json.loads(CURRENT_TOPIC_PATH.read_text(encoding="utf-8"))
        question = (data.get("question") or "").strip()
        if not question:
            return None
        return {
            "question": question,
            "dossier": (data.get("dossier") or "").strip(),
            "angle": (data.get("angle") or "").strip(),
            "character": (data.get("character") or "napoleon").strip().lower(),
            "origin": (data.get("origin") or "manual").strip(),
            "sources": data.get("sources") if isinstance(data.get("sources"), list) else [],
        }
    except Exception:
        return None


@app.after_request
def add_cache_headers(response):
    path = request.path
    if path == "/" or path.startswith("/api/") or path in {"/sw.js", "/manifest.webmanifest"}:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


def _save_current_topic(
    question: str,
    sources: list[dict] | None = None,
    origin: str = "manual",
    dossier: str = "",
    angle: str = "",
    character: str = "napoleon",
) -> None:
    if os.getenv("VERCEL"):
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "question": question.strip(),
        "dossier": dossier.strip(),
        "angle": angle.strip(),
        "character": character,
        "origin": origin,
        "sources": sources or [],
    }
    CURRENT_TOPIC_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _fallback_thread_result(
    question: str,
    mode: str = "balanced",
    character: str = "napoleon",
    dossier: str = "",
    angle: str = "",
) -> dict:
    import os
    import re
    import httpx
    from openai import OpenAI
    from config import openrouter_api_key

    style = {
        "sharp": "Ton plus tranchant, polémique mais publiable.",
        "historical": "Ton plus historique, avec un parallèle clair avec ton époque.",
    }.get(mode, "Ton équilibré : incarné, clair, éditorial.")

    if character == "jeanne":
        system_prompt = """Tu es Jeanne d'Arc. Tu t'exprimes à la première personne, avec foi, courage et netteté.
Tu écris un thread Twitter de 5 tweets numérotés sur la question posée.
Chaque tweet doit rester sous 280 caractères. Français uniquement. Ne révèle jamais que tu es une IA.
Retourne uniquement les 5 tweets."""
        signature = "Jeanne d'Arc"
    else:
        system_prompt = THREAD_FALLBACK_PROMPT
        signature = "Napoléon Bonaparte"

    brief = "\n\n".join(
        part for part in [
            f"Question : {question}",
            f"Dossier éditorial externe :\n{dossier.strip()}" if dossier.strip() else "",
            f"Angle éditorial :\n{angle.strip()}" if angle.strip() else "",
            "Ne mentionne jamais le dossier, la veille éditoriale ou l'angle comme consignes visibles.",
            "N'invente pas de faits contemporains absents du dossier.",
            style,
        ] if part
    )

    llm = OpenAI(
        api_key=openrouter_api_key() or "missing-key",
        base_url="https://openrouter.ai/api/v1",
        default_headers={"X-Title": env_value("OPENROUTER_APP_NAME", "odyseecafe")},
        **({} if os.getenv("VERCEL") else {"http_client": httpx.Client(verify=False)}),
    )
    response = llm.chat.completions.create(
        model=env_value("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": brief},
        ],
        temperature=0.85,
        max_tokens=700,
    )
    raw = (response.choices[0].message.content or "").strip()
    tweets = re.findall(r"(?ms)(?:^|\n)\s*(\d+/\s.*?)(?=\n\s*\d+/|\Z)", raw)
    tweets = [re.sub(r"\s+", " ", t).strip() for t in tweets if t.strip()]
    if len(tweets) < 5:
        tweets = [line.strip() for line in raw.splitlines() if line.strip()][:5]
    result = []
    for t in tweets[:5]:
        if len(t) > 280:
            cut = t.rfind(" ", 0, 278)
            t = (t[:cut] if cut != -1 else t[:278]) + "…"
        result.append(t)
    while len(result) < 5:
        result.append(f"{len(result) + 1}/ — {signature}")
    return {"tweets": result, "sources": [], "mode": mode}


@app.route("/")
def index():
    import json

    state       = _get_thread_state()
    chunk_count = 0
    if not os.getenv("VERCEL"):
        try:
            from query import collection
            chunk_count = collection.count()
        except Exception:
            chunk_count = 0

    model = env_value("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")

    return render_template_string(
        HTML,
        characters      = CHARACTERS,
        characters_json = json.dumps(CHARACTERS),
        active_id       = "napoleon",
        question        = state["question"],
        dossier         = state["dossier"],
        dossier_placeholder = DOSSIER_PLACEHOLDER,
        angle           = state["angle"],
        tweets          = list(enumerate(state["tweets"], 1)),
        sources         = state["sources"],
        editorial_themes= list_editorial_themes("napoleon"),
        chunk_count     = chunk_count,
        model           = model,
        app_version     = APP_VERSION,
    )


@app.route("/dossier")
def dossier_page():
    current_topic = _load_current_topic() or _get_thread_state()
    question = (current_topic or {}).get("question") or "Aucun sujet du jour."
    sources = (current_topic or {}).get("sources") or []
    dossier = (current_topic or {}).get("dossier") or ""
    angle = (current_topic or {}).get("angle") or ""
    origin = (current_topic or {}).get("origin") or "manual"
    character = (current_topic or {}).get("character") or "napoleon"

    return render_template_string(
        DOSSIER_HTML,
        question=question,
        question_json=json.dumps(question, ensure_ascii=False),
        sources=sources,
        sources_json=json.dumps(sources, ensure_ascii=False),
        character_json=json.dumps(character, ensure_ascii=False),
        dossier=dossier,
        dossier_placeholder=DOSSIER_PLACEHOLDER,
        angle=angle,
        origin=origin,
    )


@app.route("/manifest.webmanifest")
def manifest():
    return jsonify(
        name="OdyséeCafé",
        short_name="OdyséeCafé",
        start_url="/",
        display="standalone",
        background_color="#080f1a",
        theme_color="#080f1a",
        orientation="portrait",
        icons=[],
    )


@app.route("/sw.js")
def service_worker():
    js = """
const CACHE = 'odyseecafe-shell-__APP_VERSION__';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin) return;

  if (event.request.mode === 'navigate' || url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(event.request, {cache: 'no-store'}));
    return;
  }

  event.respondWith(
    fetch(event.request, {cache: 'no-store'}).catch(() => caches.match(event.request))
  );
});
""".replace("__APP_VERSION__", APP_VERSION)
    return Response(js, mimetype="application/javascript")


@app.route("/api/thread", methods=["POST"])
def api_thread():
    try:
        data = request.get_json(silent=True) or {}
        q = (data.get("question") or "").strip()
        dossier = (data.get("dossier") or "").strip()
        angle = (data.get("angle") or "").strip()
        character = (data.get("character") or "napoleon").strip().lower()
        if character not in {"napoleon", "jeanne"}:
            character = "napoleon"
        mode = (data.get("mode") or "balanced").strip()
        if mode not in {"balanced", "sharp", "historical"}:
            mode = "balanced"
        if not q:
            return jsonify(ok=False, error="Sujet vide"), 400
        try:
            from daily_napoleon_tweet import character_thread_result
            result = character_thread_result(
                q,
                character=character,
                mode=mode,
                dossier=dossier,
                angle=angle,
            )
        except Exception:
            result = _fallback_thread_result(
                q,
                mode=mode,
                character=character,
                dossier=dossier,
                angle=angle,
            )
        _thread_state["question"] = q
        _thread_state["tweets"]   = result["tweets"]
        _thread_state["sources"]  = result["sources"]
        _thread_state["mode"]     = result["mode"]
        _thread_state["dossier"]  = dossier
        _thread_state["angle"]    = angle
        _thread_state["character"] = character
        _save_current_topic(
            q,
            result["sources"],
            origin="thread",
            dossier=dossier,
            angle=angle,
            character=character,
        )
        return jsonify(
            ok=True,
            question=q,
            dossier=dossier,
            angle=angle,
            character=character,
            tweets=result["tweets"],
            sources=result["sources"],
            mode=result["mode"],
        )
    except Exception as e:
        return jsonify(ok=False, error=str(e))


@app.route("/api/topic", methods=["GET", "POST"])
def api_topic():
    if request.method == "GET":
        state = _get_thread_state()
        return jsonify(
            ok=True,
            question=state["question"],
            dossier=state["dossier"],
            angle=state["angle"],
            character=state["character"],
            sources=state["sources"],
            mode=state["mode"],
        )

    data = request.get_json(silent=True) or {}
    q = (data.get("question") or "").strip()
    if not q:
        return jsonify(ok=False, error="Question vide"), 400

    dossier = (data.get("dossier") or "").strip()
    angle = (data.get("angle") or "").strip()
    character = (data.get("character") or "napoleon").strip().lower()
    if character not in {"napoleon", "jeanne"}:
        character = "napoleon"
    sources = data.get("sources") if isinstance(data.get("sources"), list) else []
    origin = (data.get("origin") or "manual").strip()[:40]
    _thread_state["question"] = q
    _thread_state["tweets"] = [""] * 5
    _thread_state["sources"] = sources
    _thread_state["mode"] = "balanced"
    _thread_state["dossier"] = dossier
    _thread_state["angle"] = angle
    _thread_state["character"] = character
    _save_current_topic(
        q,
        sources,
        origin=origin,
        dossier=dossier,
        angle=angle,
        character=character,
    )
    return jsonify(
        ok=True,
        question=q,
        dossier=dossier,
        angle=angle,
        character=character,
        sources=sources,
    )


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    msg  = (data.get("message") or "").strip()
    character = (data.get("character") or "napoleon").strip().lower()
    if character not in {"napoleon", "jeanne"}:
        character = "napoleon"
    if not msg:
        return jsonify(ok=False, error="Message vide")
    try:
        from chat import chat as character_chat
        reply = character_chat(msg, character=character)
        return jsonify(ok=True, reply=reply)
    except Exception as e:
        return jsonify(ok=False, error=str(e))


if __name__ == "__main__":
    import webbrowser, threading
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    print(f"\n[OdyséeCafé] http://localhost:{port}\n")
    app.run(host=host, port=port, debug=False)
