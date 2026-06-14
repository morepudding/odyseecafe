"""
webapp.py - Dashboard chat-only OdyséeCafé.

Usage : python src/webapp.py -> http://localhost:5000
"""

import json
import os
import secrets
import sys
from pathlib import Path

from flask import Flask, Response, jsonify, render_template_string, request

sys.path.insert(0, str(Path(__file__).parent))

from config import env_value, load_local_env

load_local_env(Path(__file__).parent.parent / ".env.local")

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

APP_VERSION = (
    os.getenv("VERCEL_GIT_COMMIT_SHA")
    or os.getenv("VERCEL_GIT_COMMIT_REF")
    or "local"
)[:12]

CHARACTERS = [
    {"id": "napoleon", "name": "Napoléon Bonaparte", "emoji": "⚔️", "active": True, "era": "1769 - 1821"},
    {"id": "jeanne", "name": "Jeanne d'Arc", "emoji": "🛡️", "active": True, "era": "1412 - 1431"},
    {"id": "antoinette", "name": "Marie-Antoinette", "emoji": "👑", "active": False, "era": "1755 - 1793"},
    {"id": "voltaire", "name": "Voltaire", "emoji": "✒️", "active": False, "era": "1694 - 1778"},
    {"id": "robespierre", "name": "Robespierre", "emoji": "🗡️", "active": False, "era": "1758 - 1794"},
]

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
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/favicon.svg">
  <title>OdyséeCafé</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      min-height: 100vh;
      display: flex;
      background: #080f1a;
      color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      -webkit-font-smoothing: antialiased;
    }

    .sidebar {
      width: 220px;
      min-height: 100vh;
      flex-shrink: 0;
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      padding: 1.25rem .75rem;
      background: #0d1829;
      border-right: 1px solid #1e2d45;
    }

    .sidebar-logo {
      padding: .25rem .5rem .75rem;
      margin-bottom: 1rem;
      border-bottom: 1px solid #1e2d45;
      color: #f59e0b;
      font-size: 1.1rem;
      font-weight: 800;
    }
    .sidebar-logo span {
      display: block;
      margin-top: .1rem;
      color: #64748b;
      font-size: .75rem;
      font-weight: 400;
    }

    .section-label {
      padding: .4rem .5rem .3rem;
      color: #475569;
      font-size: .65rem;
      font-weight: 700;
      letter-spacing: .12em;
      text-transform: uppercase;
    }

    .char-item {
      display: flex;
      align-items: center;
      gap: .6rem;
      padding: .55rem .6rem;
      margin-bottom: 2px;
      border-radius: 8px;
      cursor: pointer;
      transition: background .15s;
    }
    .char-item:hover { background: #1e2d45; }
    .char-item.active { background: #1e3a5f; }
    .char-item.locked { opacity: .45; cursor: default; }
    .char-item.locked:hover { background: transparent; }
    .char-emoji { width: 24px; flex-shrink: 0; text-align: center; font-size: 1.1rem; }
    .char-info { flex: 1; min-width: 0; }
    .char-name {
      display: block;
      overflow: hidden;
      color: #f8fafc;
      font-size: .82rem;
      font-weight: 650;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .char-era { display: block; color: #64748b; font-size: .68rem; }
    .char-badge {
      flex-shrink: 0;
      padding: .1rem .35rem;
      border-radius: 999px;
      font-size: .6rem;
      font-weight: 750;
    }
    .badge-live { background: #14532d; color: #86efac; }
    .badge-soon { background: #1e2d45; color: #475569; }

    .main {
      width: min(100%, 820px);
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
      padding: 2rem;
    }

    .char-header {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .char-avatar {
      width: 52px;
      height: 52px;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      background: linear-gradient(135deg, #f59e0b, #b45309);
      font-size: 1.55rem;
    }
    .char-header h1 { font-size: 1.3rem; font-weight: 800; }
    .char-header .meta { margin-top: 2px; color: #64748b; font-size: .8rem; }

    .coming-soon {
      display: none;
      padding: 3rem 2rem;
      border: 1px dashed #1e2d45;
      border-radius: 14px;
      background: #0d1829;
      color: #64748b;
      text-align: center;
    }
    .coming-soon.visible { display: block; }
    .coming-soon h2 { margin-bottom: .5rem; color: #94a3b8; font-size: 1rem; }

    .stats-bar {
      display: flex;
      gap: .65rem;
      flex-wrap: wrap;
    }
    .stat-chip {
      padding: .45rem .8rem;
      border: 1px solid #1e2d45;
      border-radius: 8px;
      background: #0d1829;
      color: #94a3b8;
      font-size: .78rem;
    }
    .stat-chip strong { color: #f1f5f9; }

    .chat-shell {
      border: 1px solid #1e2d45;
      border-radius: 12px;
      background: #0d1829;
      overflow: hidden;
    }
    .chat-messages {
      height: 560px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: .8rem;
      padding: 1rem;
    }
    .chat-messages::-webkit-scrollbar { width: 4px; }
    .chat-messages::-webkit-scrollbar-track { background: transparent; }
    .chat-messages::-webkit-scrollbar-thumb { background: #1e2d45; border-radius: 2px; }

    .msg { display: flex; gap: .6rem; align-items: flex-start; }
    .msg.user { flex-direction: row-reverse; }
    .msg-avatar {
      width: 30px;
      height: 30px;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      font-size: .9rem;
    }
    .msg.napoleon .msg-avatar { background: linear-gradient(135deg, #f59e0b, #b45309); }
    .msg.jeanne .msg-avatar { background: linear-gradient(135deg, #6366f1, #3730a3); }
    .msg.user .msg-avatar { background: #1e2d45; }
    .msg-name {
      margin-bottom: .2rem;
      color: #475569;
      font-size: .65rem;
    }
    .msg-bubble {
      max-width: 80%;
      padding: .68rem .9rem;
      border-radius: 12px;
      font-size: .9rem;
      line-height: 1.55;
      white-space: pre-wrap;
    }
    .msg.napoleon .msg-bubble,
    .msg.jeanne .msg-bubble {
      border: 1px solid #1e3a5f;
      background: #0f2340;
      color: #e2e8f0;
    }
    .msg.user .msg-bubble { background: #1d4ed8; color: white; }

    .chat-input-row {
      display: flex;
      gap: .6rem;
      padding: .75rem;
      border-top: 1px solid #1e2d45;
    }
    .chat-input {
      height: 44px;
      flex: 1;
      resize: none;
      padding: .6rem .85rem;
      border: 1px solid #1e2d45;
      border-radius: 8px;
      outline: none;
      background: #080f1a;
      color: #e2e8f0;
      font: inherit;
      line-height: 1.4;
    }
    .chat-input:focus { border-color: #3b82f6; }
    .btn-send {
      width: 44px;
      height: 44px;
      flex-shrink: 0;
      border: 0;
      border-radius: 8px;
      background: #f59e0b;
      color: #080f1a;
      cursor: pointer;
      font-size: 1rem;
      font-weight: 800;
      transition: opacity .15s;
    }
    .btn-send:hover { opacity: .85; }
    .btn-send:disabled { opacity: .35; cursor: not-allowed; }

    .typing-dot {
      display: inline-block;
      width: 6px;
      height: 6px;
      margin: 0 2px;
      border-radius: 50%;
      background: #64748b;
      animation: blink 1.2s infinite;
    }
    .typing-dot:nth-child(2) { animation-delay: .2s; }
    .typing-dot:nth-child(3) { animation-delay: .4s; }
    @keyframes blink { 0%,80%,100% { opacity: .2; } 40% { opacity: 1; } }

    @media (max-width: 760px) {
      body {
        display: block;
        min-height: 100svh;
        overflow-x: hidden;
        padding: env(safe-area-inset-top) 0 env(safe-area-inset-bottom);
      }
      .sidebar {
        width: 100%;
        min-height: 0;
        height: auto;
        z-index: 20;
        overflow-x: auto;
        overflow-y: hidden;
        padding: .75rem .75rem .65rem;
        border-right: 0;
        border-bottom: 1px solid #1e2d45;
        white-space: nowrap;
        scrollbar-width: none;
      }
      .sidebar::-webkit-scrollbar { display: none; }
      .sidebar-logo {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: .8rem;
        padding: 0 0 .65rem;
        margin-bottom: .55rem;
        font-size: 1rem;
      }
      .sidebar-logo span { display: inline; text-align: right; }
      .section-label { display: none; }
      .sidebar .char-item {
        display: inline-flex;
        width: max-content;
        min-height: 48px;
        margin: 0 .4rem 0 0;
        vertical-align: top;
      }
      .char-info { max-width: 132px; }
      .char-era, .char-badge { display: none; }
      .main {
        width: 100%;
        padding: 1rem .85rem 1.4rem;
        gap: 1rem;
      }
      .char-header h1 { font-size: 1.12rem; }
      .char-avatar { width: 46px; height: 46px; }
      .stats-bar {
        flex-wrap: nowrap;
        overflow-x: auto;
        padding-bottom: .15rem;
        scrollbar-width: none;
      }
      .stats-bar::-webkit-scrollbar { display: none; }
      .stat-chip { flex: 0 0 auto; }
      .chat-shell { border-radius: 14px; }
      .chat-messages {
        height: calc(100svh - 285px);
        min-height: 430px;
      }
      .msg-bubble { max-width: 86vw; }
      .chat-input { font-size: 16px; }
    }
  </style>
</head>
<body>
  <nav class="sidebar">
    <div class="sidebar-logo">OdyséeCafé<span>Les immortels discutent.</span></div>
    <div class="section-label">Personnages</div>
    {% for c in characters %}
    <div class="char-item {% if c.active %}{% if c.id == active_id %}active{% endif %}{% else %}locked{% endif %}"
         {% if c.active %}onclick="selectChar('{{ c.id }}', this)"{% endif %}>
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

  <main class="main">
    <div class="char-header" id="char-header">
      <div class="char-avatar">⚔️</div>
      <div>
        <h1>Napoléon Bonaparte</h1>
        <div class="meta">1769 - 1821 · chat RAG · actif</div>
      </div>
    </div>

    <div class="coming-soon" id="coming-soon">
      <h2>Bientôt au café...</h2>
      <p>Ce personnage est en cours de construction.</p>
    </div>

    <div class="stats-bar" id="stats-bar">
      <div class="stat-chip">Corpus : <strong>{{ chunk_count }} chunks</strong></div>
      <div class="stat-chip">Modèle : <strong>{{ model }}</strong></div>
      <div class="stat-chip">RAG : <strong>{{ rag_backend }}</strong></div>
    </div>

    <div id="active-panel">
      <div class="chat-shell">
        <div class="chat-messages" id="chat-messages"></div>
        <div class="chat-input-row">
          <textarea class="chat-input" id="chat-input" placeholder="Posez votre question..."
                    onkeydown="chatKeydown(event)" rows="1"></textarea>
          <button class="btn-send" id="btn-send" onclick="sendChat()">➤</button>
        </div>
      </div>
    </div>
  </main>

  <script>
    const CHARS = {{ characters_json | safe }};
    let currentChar = CHARS.find((x) => x.id === "{{ active_id }}") || CHARS[0];

    const CHAR_GREETINGS = {
      napoleon: "J'arrive. Les vivants ont encore des questions, apparemment.",
      jeanne: "En nom de Dieu, posez votre question. Je vous répondrai.",
    };

    function escapeHTML(text) {
      return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }

    function selectChar(id, el) {
      const c = CHARS.find((x) => x.id === id);
      if (!c || !c.active) return;
      currentChar = c;

      document.querySelectorAll(".char-item").forEach((item) => item.classList.remove("active"));
      if (el) el.classList.add("active");

      document.querySelector("#char-header .char-avatar").textContent = c.emoji;
      document.querySelector("#char-header h1").textContent = c.name;
      document.querySelector("#char-header .meta").textContent = c.era + " · chat RAG · actif";

      document.getElementById("coming-soon").classList.remove("visible");
      document.getElementById("active-panel").style.display = "";
      document.getElementById("stats-bar").style.display = "";
      resetChat();
    }

    function resetChat() {
      const box = document.getElementById("chat-messages");
      box.innerHTML = "";
      appendMsg("ai", CHAR_GREETINGS[currentChar.id] || "Bonjour.");
    }

    function appendMsg(role, text) {
      const box = document.getElementById("chat-messages");
      const div = document.createElement("div");
      const isAI = role !== "user";
      div.className = "msg " + (isAI ? currentChar.id : "user");
      div.innerHTML = `
        <div class="msg-avatar">${isAI ? currentChar.emoji : "🧑"}</div>
        <div>
          <div class="msg-name">${isAI ? escapeHTML(currentChar.name) : "Vous"}</div>
          <div class="msg-bubble">${escapeHTML(text)}</div>
        </div>`;
      box.appendChild(div);
      box.scrollTop = box.scrollHeight;
      return div;
    }

    function appendTyping() {
      const box = document.getElementById("chat-messages");
      const div = document.createElement("div");
      div.className = "msg " + currentChar.id;
      div.id = "typing-indicator";
      div.innerHTML = `
        <div class="msg-avatar">${currentChar.emoji}</div>
        <div>
          <div class="msg-name">${escapeHTML(currentChar.name)}</div>
          <div class="msg-bubble">
            <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
          </div>
        </div>`;
      box.appendChild(div);
      box.scrollTop = box.scrollHeight;
    }

    function removeTyping() {
      const el = document.getElementById("typing-indicator");
      if (el) el.remove();
    }

    function sendChat() {
      const input = document.getElementById("chat-input");
      const msg = input.value.trim();
      if (!msg) return;

      input.value = "";
      appendMsg("user", msg);

      const btn = document.getElementById("btn-send");
      btn.disabled = true;
      appendTyping();

      fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: msg, character: currentChar.id}),
      })
        .then((r) => r.json())
        .then((d) => {
          removeTyping();
          appendMsg("ai", d.ok ? d.reply : "Erreur : " + d.error);
          btn.disabled = false;
        })
        .catch(() => {
          removeTyping();
          appendMsg("ai", "Impossible de contacter le serveur.");
          btn.disabled = false;
        });
    }

    function chatKeydown(e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendChat();
      }
    }

    if ("serviceWorker" in navigator) {
      let refreshing = false;
      navigator.serviceWorker.addEventListener("controllerchange", () => {
        if (refreshing) return;
        refreshing = true;
        window.location.reload();
      });
      navigator.serviceWorker.register("/sw.js?v={{ app_version }}").then((registration) => {
        registration.update().catch(() => {});
        if (registration.waiting) {
          registration.waiting.postMessage({type: "SKIP_WAITING"});
        }
        registration.addEventListener("updatefound", () => {
          const worker = registration.installing;
          if (!worker) return;
          worker.addEventListener("statechange", () => {
            if (worker.state === "installed" && navigator.serviceWorker.controller) {
              worker.postMessage({type: "SKIP_WAITING"});
            }
          });
        });
      }).catch(() => {});
    }

    document.addEventListener("DOMContentLoaded", () => resetChat());
  </script>
</body>
</html>
"""


@app.after_request
def add_cache_headers(response):
    path = request.path
    if path == "/" or path.startswith("/api/") or path in {"/sw.js", "/manifest.webmanifest"}:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.route("/")
def index():
    chunk_count = 0
    rag_backend = "supabase"
    try:
        from query import active_backend, corpus_chunk_count

        rag_backend = active_backend("napoleon")
        chunk_count = corpus_chunk_count("napoleon")
    except Exception:
        chunk_count = 0

    return render_template_string(
        HTML,
        characters=CHARACTERS,
        characters_json=json.dumps(CHARACTERS),
        active_id="napoleon",
        chunk_count=chunk_count,
        rag_backend=rag_backend,
        model=env_value("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash"),
        app_version=APP_VERSION,
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
        icons=[
            {
                "src": "/favicon.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any maskable",
            }
        ],
    )


@app.route("/favicon.svg")
def favicon_svg():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="96" fill="#080f1a"/>
  <circle cx="256" cy="256" r="184" fill="#111827" stroke="#d6a64f" stroke-width="18"/>
  <path d="M160 212h204a18 18 0 0 1 18 18v48a82 82 0 0 1-82 82H224a82 82 0 0 1-82-82v-48a18 18 0 0 1 18-18Z" fill="#d6a64f"/>
  <path d="M382 244h28a38 38 0 0 1 0 76h-30" fill="none" stroke="#d6a64f" stroke-width="22" stroke-linecap="round"/>
  <path d="M190 178c0-26 24-30 24-56m54 56c0-30 32-34 32-70" fill="none" stroke="#f7e0a3" stroke-width="20" stroke-linecap="round"/>
  <path d="M178 382h168" stroke="#f7e0a3" stroke-width="22" stroke-linecap="round"/>
  <path d="M194 252h126" stroke="#080f1a" stroke-width="18" stroke-linecap="round" opacity=".75"/>
</svg>"""
    return Response(svg, mimetype="image/svg+xml")


@app.route("/sw.js")
def service_worker():
    js = """
const CACHE = 'odyseecafe-shell-__APP_VERSION__';

self.addEventListener('install', () => {
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


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()
    character = (data.get("character") or "napoleon").strip().lower()
    if character not in {"napoleon", "jeanne"}:
        character = "napoleon"
    if not msg:
        return jsonify(ok=False, error="Message vide"), 400

    try:
        from chat import chat as character_chat

        reply = character_chat(msg, character=character)
        return jsonify(ok=True, reply=reply)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"\n[OdyséeCafé] http://localhost:{port}\n")
    app.run(host=host, port=port, debug=False)
