"""
webapp.py — Génère un thread Napoléon de 5 tweets et les copie dans le presse-papier.

Usage : python src/webapp.py  →  http://localhost:5000
"""

import sys
from pathlib import Path
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
sys.path.insert(0, str(Path(__file__).parent))

from daily_napoleon_tweet import napoleon_thread
from twitter_trending     import get_daily_polemic_question

app    = Flask(__name__)
_state = {"question": None, "tweets": []}

HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HistoryCafé — Thread Napoléon</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #0f172a; color: #e2e8f0;
      min-height: 100vh;
      display: flex; align-items: flex-start; justify-content: center;
      padding: 2rem;
    }
    .card {
      background: #1e293b; border-radius: 16px; padding: 2rem;
      max-width: 660px; width: 100%;
      box-shadow: 0 25px 50px rgba(0,0,0,.5);
    }
    .header { display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; }
    .avatar {
      width: 48px; height: 48px; border-radius: 50%; flex-shrink: 0;
      background: linear-gradient(135deg,#f59e0b,#d97706);
      display:flex; align-items:center; justify-content:center; font-size:1.5rem;
    }
    h1 { font-size: 1.25rem; font-weight: 700; }
    .subtitle { font-size: .85rem; color: #94a3b8; }
    .label {
      font-size: .7rem; font-weight: 700; letter-spacing:.1em;
      text-transform: uppercase; color: #64748b; margin-bottom: .5rem;
    }
    .question-box {
      background: #0f172a; border: 1px solid #334155; border-radius: 10px;
      padding: 1rem; margin-bottom: 1.75rem;
      font-size: 1rem; line-height: 1.5; color: #f1f5f9;
    }
    .thread { display: flex; flex-direction: column; gap: 0; margin-bottom: 1.75rem; }
    .tweet-row {
      display: flex; gap: .75rem; align-items: stretch;
    }
    .thread-line {
      display: flex; flex-direction: column; align-items: center;
      width: 32px; flex-shrink: 0;
    }
    .dot {
      width: 10px; height: 10px; border-radius: 50%;
      background: #f59e0b; margin-top: .85rem; flex-shrink: 0;
    }
    .vline {
      width: 2px; background: #334155; flex: 1; margin-top: 4px;
    }
    .tweet-row:last-child .vline { display: none; }
    .tweet-wrap { flex: 1; padding-bottom: 1rem; }
    .tweet-num { font-size: .7rem; color: #64748b; margin-bottom: .3rem; }
    .tweet-box {
      background: #0f172a; border: 1px solid #1d4ed8; border-radius: 10px;
      padding: .85rem 1rem;
      font-size: .92rem; line-height: 1.6; color: #e2e8f0;
      white-space: pre-wrap; outline: none;
      min-height: 3.5rem;
    }
    .tweet-box:focus { border-color: #3b82f6; }
    .tweet-footer {
      display: flex; justify-content: space-between; align-items: center;
      margin-top: .35rem;
    }
    .char-count { font-size: .72rem; color: #64748b; }
    .char-count.warn { color: #f59e0b; }
    .char-count.over { color: #ef4444; }
    .btn-copy-one {
      background: none; border: 1px solid #334155; color: #94a3b8;
      border-radius: 6px; padding: .25rem .65rem; font-size: .72rem;
      cursor: pointer; transition: all .15s;
    }
    .btn-copy-one:hover { background: #334155; color: #e2e8f0; }
    .copied { color: #86efac !important; border-color: #166534 !important; }

    .actions { display: flex; gap: .75rem; flex-wrap: wrap; }
    button.main {
      padding: .65rem 1.2rem; border: none; border-radius: 8px;
      font-size: .9rem; font-weight: 600; cursor: pointer; transition: opacity .15s;
    }
    button.main:hover { opacity: .85; }
    button.main:disabled { opacity: .4; cursor: not-allowed; }
    .btn-all   { background: #1d4ed8; color: white; flex: 1; }
    .btn-open  { background: #166534; color: #86efac; }
    .btn-regen { background: #334155; color: #e2e8f0; }
    .spinner {
      display: inline-block; width: 14px; height: 14px;
      border: 2px solid rgba(255,255,255,.3); border-top-color: white;
      border-radius: 50%; animation: spin .6s linear infinite;
      vertical-align: middle; margin-right: 6px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
<div class="card">
  <div class="header">
    <div class="avatar">⚔️</div>
    <div>
      <h1>Thread Napoléon</h1>
      <div class="subtitle">@OdyseeCafe · 5 tweets</div>
    </div>
  </div>

  <div class="label">Question du jour</div>
  <div class="question-box" id="question">{{ question }}</div>

  <div class="label">Thread (modifiable)</div>
  <div class="thread" id="thread">
    {% for i, tweet in tweets %}
    <div class="tweet-row" id="row-{{ i }}">
      <div class="thread-line">
        <div class="dot"></div>
        <div class="vline"></div>
      </div>
      <div class="tweet-wrap">
        <div class="tweet-num">Tweet {{ i }}/5</div>
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
    <button class="main btn-regen" onclick="doRegen()">🔄 Regénérer</button>
    <button class="main btn-all"   onclick="copyAll()">📋 Copier tout</button>
    <button class="main btn-open"  onclick="window.open('https://x.com/compose/post','_blank')">
      🐦 Ouvrir X
    </button>
  </div>
</div>

<script>
  function updateCount(i) {
    const box = document.getElementById('tweet-' + i);
    const cc  = document.getElementById('cc-' + i);
    const n   = box.innerText.length;
    cc.textContent = n + '/280';
    cc.className = 'char-count' + (n > 280 ? ' over' : n > 260 ? ' warn' : '');
  }

  // Init compteurs
  for (let i = 1; i <= 5; i++) updateCount(i);

  function copySingle(i) {
    const text = document.getElementById('tweet-' + i).innerText;
    navigator.clipboard.writeText(text).then(() => {
      const btn = document.querySelector(`#row-${i} .btn-copy-one`);
      const orig = btn.textContent;
      btn.textContent = '✓ Copié';
      btn.classList.add('copied');
      setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 1800);
    });
  }

  function copyAll() {
    const parts = [];
    for (let i = 1; i <= 5; i++) {
      parts.push(document.getElementById('tweet-' + i).innerText);
    }
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
    btn.innerHTML = '<span class="spinner"></span> Génération...';
    fetch('/generate', {method: 'POST'})
      .then(r => r.json())
      .then(d => {
        if (d.ok) {
          document.getElementById('question').textContent = d.question;
          d.tweets.forEach((t, idx) => {
            const i = idx + 1;
            document.getElementById('tweet-' + i).innerText = t;
            updateCount(i);
          });
        } else {
          alert('Erreur : ' + d.error);
        }
        btn.disabled = false;
        btn.innerHTML = '🔄 Regénérer';
      });
  }
</script>
</body>
</html>
"""


def _get_state():
    if not _state["question"]:
        q = get_daily_polemic_question()
        _state["question"] = q
        _state["tweets"]   = napoleon_thread(q)
    return _state


@app.route("/")
def index():
    state = _get_state()
    return render_template_string(
        HTML,
        question = state["question"],
        tweets   = list(enumerate(state["tweets"], 1)),
    )


@app.route("/generate", methods=["POST"])
def generate():
    try:
        q = get_daily_polemic_question()
        tweets = napoleon_thread(q)
        _state["question"] = q
        _state["tweets"]   = tweets
        return jsonify(ok=True, question=q, tweets=tweets)
    except Exception as e:
        return jsonify(ok=False, error=str(e))


if __name__ == "__main__":
    import webbrowser, threading
    port = 5000
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    print(f"\n[webapp] http://localhost:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=False)
