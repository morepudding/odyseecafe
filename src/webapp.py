"""
webapp.py — Dashboard OdyséeCafé

Sidebar personnages + tabs Thread / Chat pour chaque IA active.

Usage : python src/webapp.py  →  http://localhost:5000
"""

import sys
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request, session
from dotenv import load_dotenv
import secrets

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
sys.path.insert(0, str(Path(__file__).parent))

from daily_napoleon_tweet import napoleon_thread
from twitter_trending     import get_daily_polemic_question
from chat                 import chat as napoleon_chat

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

_thread_state = {"question": None, "tweets": []}

CHARACTERS = [
    {"id": "napoleon",      "name": "Napoléon Bonaparte", "emoji": "⚔️",  "active": True,  "era": "1769 – 1821"},
    {"id": "voltaire",      "name": "Voltaire",           "emoji": "✒️",  "active": False, "era": "1694 – 1778"},
    {"id": "moliere",       "name": "Molière",            "emoji": "🎭",  "active": False, "era": "1622 – 1673"},
    {"id": "chateaubriand", "name": "Chateaubriand",      "emoji": "📖",  "active": False, "era": "1768 – 1848"},
    {"id": "maurras",       "name": "Charles Maurras",    "emoji": "🏛️", "active": False, "era": "1868 – 1952"},
    {"id": "celine",        "name": "Céline",             "emoji": "🖊️", "active": False, "era": "1894 – 1961"},
    {"id": "robespierre",   "name": "Robespierre",        "emoji": "🗡️", "active": False, "era": "1758 – 1794"},
    {"id": "proudhon",      "name": "Proudhon",           "emoji": "⚙️", "active": False, "era": "1809 – 1865"},
    {"id": "bainville",     "name": "Jacques Bainville",  "emoji": "📰", "active": False, "era": "1879 – 1936"},
]

HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OdyséeCafé</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #080f1a; color: #e2e8f0;
      min-height: 100vh; display: flex;
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
  </style>
</head>
<body>

<!-- SIDEBAR -->
<nav class="sidebar">
  <div class="sidebar-logo">OdyséeCafé<span>Les immortels tweetent.</span></div>
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
      <button class="tab-btn active" onclick="switchTab('thread', this)">🧵 Thread</button>
      <button class="tab-btn"        onclick="switchTab('chat',   this)">💬 Chat</button>
    </div>

    <!-- THREAD TAB -->
    <div class="tab-panel active" id="tab-thread" style="padding-top:1.25rem">
      <div class="label">Question du jour</div>
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
        <button class="act btn-regen" onclick="doRegen()">🔄 Regénérer</button>
        <button class="act btn-all"   onclick="copyAll()">📋 Copier tout</button>
        <button class="act btn-x"     onclick="window.open('https://x.com/compose/post','_blank')">🐦 Ouvrir X</button>
      </div>
    </div>

    <!-- CHAT TAB -->
    <div class="tab-panel" id="tab-chat" style="padding-top:1.25rem">
      <div class="chat-window">
        <div class="chat-messages" id="chat-messages">
          <div class="msg napoleon">
            <div class="msg-avatar">⚔️</div>
            <div>
              <div class="msg-name">Napoléon Bonaparte</div>
              <div class="msg-bubble">Que voulez-vous savoir ? Je suis là.</div>
            </div>
          </div>
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
  const CHARS = {{ characters_json }};

  function selectChar(id) {
    const c = CHARS.find(x => x.id === id);
    if (!c || !c.active) return;

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

  function doRegen() {
    const btn = document.querySelector('.btn-regen');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Génération…';
    fetch('/api/thread', {method: 'POST'})
      .then(r => r.json())
      .then(d => {
        if (d.ok) {
          document.getElementById('question').textContent = d.question;
          d.tweets.forEach((t, idx) => {
            const i = idx + 1;
            document.getElementById('tweet-' + i).innerText = t;
            updateCount(i);
          });
        } else { alert('Erreur : ' + d.error); }
        btn.disabled = false;
        btn.innerHTML = '🔄 Regénérer';
      });
  }

  // ── CHAT ──
  const chatHistory = [];

  function appendMsg(role, text) {
    const box = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'msg ' + (role === 'user' ? 'user' : 'napoleon');
    const avatarText = role === 'user' ? '🧑' : '⚔️';
    const nameText   = role === 'user' ? 'Vous' : 'Napoléon Bonaparte';
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
    div.className = 'msg napoleon'; div.id = 'typing-indicator';
    div.innerHTML = `
      <div class="msg-avatar">⚔️</div>
      <div><div class="msg-name">Napoléon Bonaparte</div>
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
      body: JSON.stringify({message: msg}),
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
</body>
</html>
"""


# ── ROUTES ────────────────────────────────────────────────────────────────────

def _get_thread_state():
    if not _thread_state["question"]:
        q = get_daily_polemic_question()
        _thread_state["question"] = q
        _thread_state["tweets"]   = napoleon_thread(q)
    return _thread_state


@app.route("/")
def index():
    import json
    from query import collection

    state       = _get_thread_state()
    chunk_count = collection.count()

    import os
    model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")

    return render_template_string(
        HTML,
        characters      = CHARACTERS,
        characters_json = json.dumps(CHARACTERS),
        active_id       = "napoleon",
        question        = state["question"],
        tweets          = list(enumerate(state["tweets"], 1)),
        chunk_count     = chunk_count,
        model           = model,
    )


@app.route("/api/thread", methods=["POST"])
def api_thread():
    try:
        q      = get_daily_polemic_question()
        tweets = napoleon_thread(q)
        _thread_state["question"] = q
        _thread_state["tweets"]   = tweets
        return jsonify(ok=True, question=q, tweets=tweets)
    except Exception as e:
        return jsonify(ok=False, error=str(e))


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    msg  = (data.get("message") or "").strip()
    if not msg:
        return jsonify(ok=False, error="Message vide")
    try:
        reply = napoleon_chat(msg)
        return jsonify(ok=True, reply=reply)
    except Exception as e:
        return jsonify(ok=False, error=str(e))


if __name__ == "__main__":
    import webbrowser, threading
    port = 5000
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    print(f"\n[OdyséeCafé] http://localhost:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=False)
