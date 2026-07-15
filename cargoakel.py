from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import json
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'akel-cargo-secret-key-2026'

# ============ ТАНЗИМОТ ============
PRICE_PER_KG = 25  # Нархи нав: 25 сомонӣ барои 1 кг
ADMIN_USERNAME = 'Komiljon'
ADMIN_PASSWORD = 'Komiljon Orifjonzoda'
DATA_FILE = 'tracks.json'
TICKETS_FILE = 'tickets.json'

# Зинаҳои интиқол
STAGES = ['Чин', 'Роҳ', 'Тоҷикистон', 'Омода']

# ============ ПОЙГОҲИ МАЪЛУМОТ (JSON) ============
def load_tracks():
    if not os.path.exists(DATA_FILE):
        default = {
            'AKEL2026001': {'stage': 1, 'client': 'Намуна 1', 'weight': 5.2, 'updated': '2026-06-20'},
            'AKEL2026002': {'stage': 2, 'client': 'Намуна 2', 'weight': 12.5, 'updated': '2026-06-21'},
        }
        save_tracks(default)
        return default
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_tracks(tracks):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(tracks, f, ensure_ascii=False, indent=2)

def load_tickets():
    if not os.path.exists(TICKETS_FILE):
        default = {}
        save_tickets(default)
        return default
    with open(TICKETS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_tickets(tickets):
    with open(TICKETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tickets, f, ensure_ascii=False, indent=2)

# ============ ҲИМОЯИ АДМИН ============
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ============ САҲИФАИ АСОСӢ ============
INDEX_HTML = r"""<!DOCTYPE html>
<html lang="tg">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AKEL CARGO — Карго аз Чин ба Тоҷикистон</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', Tahoma, sans-serif; }
body { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); min-height:100vh; color:#fff; }
.container { max-width:1100px; margin:0 auto; padding:20px; }

/* Header */
header { text-align:center; padding:40px 0 30px; }
header h1 { font-size:48px; font-weight:900; letter-spacing:2px; text-shadow:2px 2px 8px rgba(0,0,0,0.3); }
header h1 .logo-accent { color:#ffd700; }
header p { font-size:18px; margin-top:10px; opacity:0.9; }

/* Nav */
nav { display:flex; justify-content:center; gap:10px; flex-wrap:wrap; margin:20px 0 30px; }
nav a { background:rgba(255,255,255,0.15); color:#fff; padding:10px 20px; border-radius:25px; text-decoration:none; transition:all 0.3s; backdrop-filter:blur(10px); }
nav a:hover { background:#ffd700; color:#1e3c72; transform:translateY(-2px); }

/* Cards */
.card { background:rgba(255,255,255,0.95); color:#222; border-radius:20px; padding:30px; margin-bottom:25px; box-shadow:0 10px 40px rgba(0,0,0,0.2); }
.card h2 { color:#1e3c72; margin-bottom:20px; font-size:26px; display:flex; align-items:center; gap:10px; }

/* Track Search */
.track-form { display:flex; gap:10px; flex-wrap:wrap; }
.track-form input, .ticket-form input, .ticket-form textarea { flex:1; min-width:250px; padding:14px 18px; border:2px solid #ddd; border-radius:10px; font-size:16px; outline:none; transition:border 0.3s; }
.track-form input:focus { border-color:#1e3c72; }
.btn { background:linear-gradient(135deg,#1e3c72,#2a5298); color:#fff; border:none; padding:14px 30px; border-radius:10px; font-size:16px; font-weight:600; cursor:pointer; transition:all 0.3s; }
.btn:hover { transform:translateY(-2px); box-shadow:0 5px 15px rgba(30,60,114,0.4); }

/* Timeline */
.timeline { display:flex; justify-content:space-between; align-items:center; margin:40px 0 20px; position:relative; padding:0 20px; }
.timeline::before { content:''; position:absolute; top:30px; left:60px; right:60px; height:4px; background:#e0e0e0; z-index:0; }
.timeline-progress { position:absolute; top:30px; left:60px; height:4px; background:linear-gradient(90deg,#1e3c72,#ffd700); z-index:1; width:0%; transition:width 1.5s ease; }
.stage { position:relative; z-index:2; text-align:center; flex:1; }
.stage-circle { width:60px; height:60px; border-radius:50%; background:#e0e0e0; color:#999; margin:0 auto 10px; display:flex; align-items:center; justify-content:center; font-size:24px; font-weight:bold; border:4px solid #fff; box-shadow:0 4px 10px rgba(0,0,0,0.15); transition:all 0.5s; }
.stage.active .stage-circle { background:linear-gradient(135deg,#1e3c72,#2a5298); color:#fff; transform:scale(1.15); }
.stage.current .stage-circle { background:linear-gradient(135deg,#ffd700,#ffaa00); color:#1e3c72; animation:pulse 1.5s infinite; }
@keyframes pulse { 0%,100% { box-shadow:0 0 0 0 rgba(255,215,0,0.7); } 50% { box-shadow:0 0 0 15px rgba(255,215,0,0); } }
.stage-label { font-size:14px; font-weight:600; color:#555; }
.stage.active .stage-label { color:#1e3c72; }

.result-info { background:#f0f7ff; border-left:4px solid #1e3c72; padding:15px; border-radius:10px; margin-top:20px; }
.result-info p { margin:5px 0; color:#333; }
.result-error { background:#ffe6e6; border-left:4px solid #d9534f; padding:15px; border-radius:10px; margin-top:20px; color:#a00; }

/* Calculator */
.calc-grid { display:grid; grid-template-columns:1fr 1fr; gap:15px; margin-bottom:20px; }
.calc-grid label { display:block; font-weight:600; color:#1e3c72; margin-bottom:8px; }
.calc-grid input { width:100%; padding:12px; border:2px solid #ddd; border-radius:10px; font-size:16px; outline:none; }
.calc-grid input:focus { border-color:#1e3c72; }
.calc-result { background:linear-gradient(135deg,#1e3c72,#2a5298); color:#fff; padding:25px; border-radius:15px; text-align:center; margin-top:20px; }
.calc-result .price { font-size:42px; font-weight:900; color:#ffd700; margin:10px 0; }
.calc-result .detail { font-size:14px; opacity:0.9; }
@media(max-width:600px){ .calc-grid{grid-template-columns:1fr;} header h1{font-size:32px;} .timeline-progress{left:40px;} .timeline::before{left:40px;right:40px;} }

/* Address */
.address-box { background:#f8f9fa; border:2px solid #e0e0e0; border-radius:12px; padding:20px; margin-bottom:15px; }
.address-box h3 { color:#1e3c72; margin-bottom:10px; display:flex; align-items:center; gap:8px; }
.address-text { background:#fff; padding:12px; border-radius:8px; font-family:monospace; word-break:break-all; margin-bottom:10px; color:#333; }
.copy-btn { background:#1e3c72; color:#fff; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; font-size:14px; }
.copy-btn:hover { background:#2a5298; }
.copy-btn.copied { background:#28a745; }

/* FAQ */
.faq-item { background:#f8f9fa; border-radius:10px; margin-bottom:10px; overflow:hidden; }
.faq-question { padding:15px 20px; cursor:pointer; font-weight:600; color:#1e3c72; display:flex; justify-content:space-between; align-items:center; user-select:none; }
.faq-question:hover { background:#e8f0fe; }
.faq-answer { padding:0 20px; max-height:0; overflow:hidden; transition:all 0.3s ease; color:#555; }
.faq-item.active .faq-answer { padding:0 20px 15px; max-height:200px; }
.faq-item.active .faq-question .arrow { transform:rotate(180deg); }
.arrow { transition:transform 0.3s; }

/* Ticket Support */
.ticket-form { display: flex; flex-direction: column; gap: 12px; margin-bottom: 25px; }
.ticket-form input, .ticket-form textarea { width: 100%; border: 2px solid #ddd; border-radius: 10px; color: #333;}
.ticket-form textarea { resize: vertical; min-height: 100px; }
.tickets-list { margin-top: 20px; max-height: 400px; overflow-y: auto; }

/* Contact */
.contact-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:15px; }
.contact-card { background:#f8f9fa; padding:20px; border-radius:12px; text-align:center; text-decoration:none; color:#1e3c72; transition:all 0.3s; border:2px solid transparent; }
.contact-card:hover { transform:translateY(-3px); border-color:#1e3c72; box-shadow:0 5px 15px rgba(30,60,114,0.2); }
.contact-card .icon { font-size:36px; margin-bottom:8px; }
.contact-card .label { font-weight:600; }
.contact-card .value { font-size:14px; color:#666; margin-top:4px; }

footer { text-align:center; padding:30px 0; opacity:0.8; font-size:14px; }
footer a { color:#ffd700; text-decoration:none; }
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>AKEL <span class="logo-accent">CARGO</span></h1>
    <p>📦 Карго аз Чин ба Тоҷикистон • Зуд, бехатар, арзон</p>
  </header>

  <nav>
    <a href="#track">🔍 Санҷиши трек</a>
    <a href="#calc">💰 Калкулятор</a>
    <a href="#address">📍 Адрес</a>
    <a href="#ticket-sec">✉️ Саволу Ҷавоб</a>
    <a href="#contact">📞 Тамос</a>
  </nav>

  <!-- Track Search -->
  <div class="card" id="track">
    <h2>🔍 Санҷиши трек-код</h2>
    <p style="color:#666;margin-bottom:15px">Трек-кодатонро ворид кунед то ҷойгиршавии бори худро бубинед</p>
    <div class="track-form">
      <input type="text" id="trackInput" placeholder="Масалан: AKEL2026001" autocomplete="off">
      <button class="btn" onclick="searchTrack()">Ҷустуҷӯ</button>
    </div>
    <div id="trackResult"></div>
  </div>

  <!-- Calculator -->
  <div class="card" id="calc">
    <h2>💰 Калкулятори нарх</h2>
    <p style="color:#666;margin-bottom:15px">Нархи 1 кг — <strong style="color:#1e3c72">25 сомонӣ</strong></p>
    <div class="calc-grid">
      <div>
        <label>Вазн (кг)</label>
        <input type="number" id="calcWeight" placeholder="Масалан: 5.5" step="0.1" min="0" oninput="calculate()">
      </div>
      <div>
        <label>Миқдори бастаҳо</label>
        <input type="number" id="calcQty" placeholder="Масалан: 2" min="1" value="1" oninput="calculate()">
      </div>
    </div>
    <div class="calc-result">
      <div class="detail">Нархи умумӣ</div>
      <div class="price" id="calcPrice">0 сомонӣ</div>
      <div class="detail" id="calcDetail">Вазнро ворид кунед</div>
    </div>
  </div>

  <!-- Support Tickets Section -->
  <div class="card" id="ticket-sec">
    <h2>✉️ Маркази Дастгирӣ ва Саволҳо (Тикет)</h2>
    <p style="color:#666;margin-bottom:15px">Саволи худро нависед, админ фавран ба он ҷавоб хоҳад дод!</p>
    <form class="ticket-form" id="ticketForm" onsubmit="submitTicket(event)">
      <input type="text" id="ticketName" placeholder="Номи шумо" required style="color:#222;">
      <input type="text" id="ticketContact" placeholder="Телефон ё Telegram барои тамос" required style="color:#222;">
      <textarea id="ticketQuestion" placeholder="Саволи худро дар ин ҷо муфассал нависед..." required style="color:#222;"></textarea>
      <button type="submit" class="btn">✈️ Фиристодани савол</button>
    </form>
    
    <h3 style="color:#1e3c72; margin-top:20px; border-top:1px solid #eee; padding-top:15px;">💬 Саволҳо ва Ҷавобҳои охирин:</h3>
    <div id="ticketsList" class="tickets-list">
      <!-- Ҷавобҳо ба таври худкор бор мешаванд -->
    </div>
  </div>

  <!-- Address -->
  <div class="card" id="address">
    <h2>📍 Адреси анбор</h2>

    <div class="address-box">
      <h3>🇨🇳 Анбор дар Чин</h3>
      <div class="address-text" id="addrChina">KHMIR 15625450102
浙江省金华市义乌市 商城大道与柳青路交叉口东北220米洪华小区102栋2单元一楼
(MIR nom tel)</div>
      <button class="copy-btn" onclick="copyText('addrChina', this)">📋 Нусхабардорӣ</button>
    </div>

    <div class="address-box">
      <h3>🇹🇯 Анбор дар Тоҷикистон (Истаравшан)</h3>
      <div class="address-text" id="addrTj">ш. Истаравшан, AKEL CARGO
кӯчаи марказӣ, наздикии бозори марказӣ
Тел: +992 71 555 50 00</div>
      <button class="copy-btn" onclick="copyText('addrTj', this)">📋 Нусхабардорӣ</button>
    </div>
  </div>

  <!-- FAQ -->
  <div class="card" id="faq">
    <h2>❓ Саволу ҷавобҳои умумӣ</h2>
    <div class="faq-item">
      <div class="faq-question" onclick="toggleFaq(this)">Бор чанд рӯз меояд?<span class="arrow">▼</span></div>
      <div class="faq-answer">Одатан 15-25 рӯз. Аз Чин ба Тоҷикистон вобаста ба мавсим ва намуди бор.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question" onclick="toggleFaq(this)">Нархи интиқол чанд аст?<span class="arrow">▼</span></div>
      <div class="faq-answer">25 сомонӣ барои 1 кг. Барои борҳои калон тахфиф пешбинӣ шудааст. Калкулятори моро истифода баред.</div>
    </div>
  </div>

  <!-- Contact -->
  <div class="card" id="contact">
    <h2>📞 Бо мо тамос гиред</h2>
    <div class="contact-grid">
      <a href="https://t.me/AKELCARGO" class="contact-card" target="_blank">
        <div class="icon">✈️</div>
        <div class="label">Telegram</div>
        <div class="value">@AKELCARGO</div>
      </a>
      <a href="tel:+992715555000" class="contact-card">
        <div class="icon">📞</div>
        <div class="label">Телефон</div>
        <div class="value">+992 71 555 50 00</div>
      </a>
      <a href="/admin" class="contact-card">
        <div class="icon">🔐</div>
        <div class="label">Админ панел</div>
        <div class="value">Воридшавӣ</div>
      </a>
    </div>
  </div>

  <footer>
    <p>© 2026 AKEL CARGO. Ҳамаи ҳуқуқҳо ҳифз карда шудаанд.</p>
  </footer>
</div>

<script>
const STAGES = ['Чин', 'Роҳ', 'Тоҷикистон', 'Омода'];

async function searchTrack(){
  const code = document.getElementById('trackInput').value.trim().toUpperCase();
  const resultDiv = document.getElementById('trackResult');
  if(!code){
    resultDiv.innerHTML = '<div class="result-error">Лутфан трек-кодро ворид кунед</div>';
    return;
  }
  resultDiv.innerHTML = '<div style="text-align:center;padding:20px;color:#666">⏳ Ҷустуҷӯ...</div>';
  try {
    const res = await fetch('/api/track/' + encodeURIComponent(code));
    const data = await res.json();
    if(!data.found){
      resultDiv.innerHTML = '<div class="result-error">❌ Трек-код ёфт нашуд. Лутфан санҷед ё бо мо тамос гиред.</div>';
      return;
    }
    renderTimeline(data, resultDiv);
  } catch(e){
    resultDiv.innerHTML = '<div class="result-error">Хатогии сервер</div>';
  }
}

function renderTimeline(data, container){
  const stage = data.stage;
  let html = '<div class="timeline">';
  html += '<div class="timeline-progress" id="tlProgress"></div>';
  STAGES.forEach((name, idx) => {
    let cls = 'stage';
    if(idx < stage) cls += ' active';
    else if(idx === stage) cls += ' active current';
    const icon = idx === 0 ? '🇨🇳' : idx === 1 ? '🚚' : idx === 2 ? '🇹🇯' : '✅';
    html += `<div class="${cls}"><div class="stage-circle">${icon}</div><div class="stage-label">${name}</div></div>`;
  });
  html += '</div>';
  html += '<div class="result-info">';
  html += '<p><strong>Трек-код:</strong> ' + (data.code || '') + '</p>';
  if(data.client) html += '<p><strong>Мизоҷ:</strong> ' + data.client + '</p>';
  if(data.weight) html += '<p><strong>Вазн:</strong> ' + data.weight + ' кг</p>';
  html += '<p><strong>Ҳолат:</strong> ' + STAGES[stage] + (stage === 3 ? ' — Бор омода аст!' : '') + '</p>';
  if(data.updated) html += '<p><strong>Навсозӣ:</strong> ' + data.updated + '</p>';
  html += '</div>';
  container.innerHTML = html;
  setTimeout(() => {
    const progress = (stage / (STAGES.length - 1)) * 100;
    document.getElementById('tlProgress').style.width = progress + '%';
  }, 100);
}

function calculate(){
  const w = parseFloat(document.getElementById('calcWeight').value) || 0;
  const q = parseInt(document.getElementById('calcQty').value) || 1;
  const total = w * q * 25;
  document.getElementById('calcPrice').textContent = total.toFixed(2) + ' сомонӣ';
  if(w > 0){
    document.getElementById('calcDetail').textContent = `${w} кг × ${q} баста × 25 сомонӣ`;
  } else {
    document.getElementById('calcDetail').textContent = 'Вазнро ворид кунед';
  }
}

function copyText(id, btn){
  const text = document.getElementById(id).innerText;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = '✅ Нусхабардорӣ шуд';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = '📋 Нусхабардорӣ';
      btn.classList.remove('copied');
    }, 2000);
  });
}

function toggleFaq(el){
  const item = el.parentElement;
  item.classList.toggle('active');
}

// Функсияҳо барои Тикетҳо
async function loadTickets(){
  try {
    const res = await fetch('/api/tickets');
    const data = await res.json();
    const listDiv = document.getElementById('ticketsList');
    if(!data.length){
      listDiv.innerHTML = '<p style="color:#666;text-align:center;">Ҳоло ягон савол нест.</p>';
      return;
    }
    let html = '';
    data.forEach(t => {
      html += `<div style="background:#fff; padding:15px; border-radius:10px; margin-bottom:10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-left:4px solid ${t.status === 'answered' ? '#28a745' : '#ffaa00'}">`;
      html += `<div style="display:flex; justify-content:space-between; margin-bottom:5px;"><strong style="color:#1e3c72">${t.name}</strong><span style="font-size:12px; color:#999">${t.created_at}</span></div>`;
      html += `<p style="color:#333; margin-bottom:8px;"><strong>Савол:</strong> ${t.question}</p>`;
      if(t.status === 'answered'){
        html += `<div style="background:#e8f5e9; padding:10px; border-radius:8px; margin-top:5px; color:#1b5e20;"><strong>💬 Ҷавоби AKEL CARGO:</strong> ${t.answer}</div>`;
      } else {
        html += `<p style="font-size:13px; color:#f57c00; font-style:italic;">⏳ Дар интизори ҷавоби админ...</p>`;
      }
      html += `</div>`;
    });
    listDiv.innerHTML = html;
  } catch(e) {
    console.error(e);
  }
}

async function submitTicket(e){
  e.preventDefault();
  const name = document.getElementById('ticketName').value.trim();
  const contact = document.getElementById('ticketContact').value.trim();
  const question = document.getElementById('ticketQuestion').value.trim();
  
  const formData = new FormData();
  formData.append('name', name);
  formData.append('contact', contact);
  formData.append('question', question);
  
  try {
    const res = await fetch('/api/ticket/add', { method: 'POST', body: formData });
    const data = await res.json();
    alert(data.msg);
    if(data.success){
      document.getElementById('ticketForm').reset();
      loadTickets();
    }
  } catch(e){
    alert('Хатогии система!');
  }
}

window.onload = () => {
  loadTickets();
};

document.getElementById('trackInput').addEventListener('keypress', e => {
  if(e.key === 'Enter') searchTrack();
});
</script>
</body>
</html>
"""

# ============ САҲИФАИ АДМИН ============
ADMIN_LOGIN_HTML = r"""<!DOCTYPE html>
<html lang="tg"><head><meta charset="UTF-8"><title>Воридшавӣ — AKEL CARGO Admin</title>
<style>
body{margin:0;font-family:Segoe UI,sans-serif;background:linear-gradient(135deg,#1e3c72,#2a5298);min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:#fff;padding:40px;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3);width:90%;max-width:400px}
h1{color:#1e3c72;text-align:center;margin-bottom:25px}
input{width:100%;padding:14px;margin-bottom:15px;border:2px solid #ddd;border-radius:10px;font-size:16px;box-sizing:border-box}
input:focus{outline:none;border-color:#1e3c72}
button{width:100%;padding:14px;background:linear-gradient(135deg,#1e3c72,#2a5298);color:#fff;border:none;border-radius:10px;font-size:16px;font-weight:600;cursor:pointer}
button:hover{transform:translateY(-2px);box-shadow:0 5px 15px rgba(30,60,114,0.4)}
.error{background:#ffe6e6;color:#a00;padding:10px;border-radius:8px;margin-bottom:15px;text-align:center}
.back{display:block;text-align:center;margin-top:15px;color:#1e3c72;text-decoration:none}
</style></head><body>
<form class="box" method="POST">
  <h1>🔐 AKEL CARGO Admin</h1>
  {% if error %}<div class="error">{{error}}</div>{% endif %}
  <input type="text" name="username" placeholder="Логин (Komiljon)" required autofocus style="color:#222;">
  <input type="password" name="password" placeholder="Парол" required style="color:#222;">
  <button type="submit">Воридшавӣ</button>
  <a href="/" class="back">← Бозгашт ба сайт</a>
</form></body></html>
"""

ADMIN_PANEL_HTML = r"""<!DOCTYPE html>
<html lang="tg"><head><meta charset="UTF-8"><title>Панели идоракунӣ — AKEL CARGO</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Segoe UI,sans-serif}
body{background:#f0f2f5;min-height:100vh}
header{background:linear-gradient(135deg,#1e3c72,#2a5298);color:#fff;padding:20px 30px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 4px 10px rgba(0,0,0,0.1)}
header h1{font-size:24px}
header a{color:#ffd700;text-decoration:none;padding:8px 16px;background:rgba(255,255,255,0.1);border-radius:8px}
.container{max-width:1200px;margin:30px auto;padding:0 20px}

/* Grid layout for Profile & Dashboard Stats */
.dashboard-layout { display: grid; grid-template-columns: 1fr 3fr; gap: 20px; margin-bottom: 25px; }
@media(max-width:900px){ .dashboard-layout { grid-template-columns: 1fr; } }

/* Profile Card */
.profile-card { background: #fff; border-radius: 15px; padding: 25px; box-shadow:0 4px 15px rgba(0,0,0,0.08); text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.profile-avatar { width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #ffd700, #ffaa00); color: #1e3c72; display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: bold; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
.profile-info h3 { color: #1e3c72; margin-bottom: 5px; font-size: 20px; }
.profile-info .role { background: #e8f0fe; color: #1e3c72; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; display: inline-block; margin-bottom: 15px; }
.profile-details p { font-size: 13px; color: #555; text-align: left; margin-bottom: 5px; width: 100%; }

/* Stats grid */
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:15px; width: 100%; }
.stat-card { background:#fff; color:#222; padding:20px; border-radius:15px; box-shadow:0 4px 15px rgba(0,0,0,0.08); border-left: 5px solid #1e3c72; }
.stat-card-gold { border-left-color: #ffd700; }
.stat-card .num { font-size:32px; font-weight:900; color:#1e3c72; }
.stat-card-gold .num { color: #d4a373; }
.stat-card .lbl { font-size:13px; color: #666; margin-top:5px; font-weight: 600; }

.card{background:#fff;border-radius:15px;padding:25px;margin-bottom:20px;box-shadow:0 4px 15px rgba(0,0,0,0.08)}
.card h2{color:#1e3c72;margin-bottom:20px;font-size:20px}
.form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;align-items:end}
.form-grid label{font-size:13px;color:#555;font-weight:600;display:block;margin-bottom:5px}
.form-grid input,.form-grid select,.form-grid textarea{width:100%;padding:10px;border:2px solid #ddd;border-radius:8px;font-size:14px}
.form-grid input:focus,.form-grid select:focus{outline:none;border-color:#1e3c72}
button{background:linear-gradient(135deg,#1e3c72,#2a5298);color:#fff;border:none;padding:10px 20px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;transition:all 0.3s}
button:hover{transform:translateY(-2px);box-shadow:0 5px 15px rgba(30,60,114,0.3)}
button.danger{background:linear-gradient(135deg,#d9534f,#c9302c)}
button.warning{background:linear-gradient(135deg,#f0ad4e,#ec971f)}
table{width:100%;border-collapse:collapse;margin-top:15px}
th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}
th{background:#f8f9fa;color:#1e3c72;font-weight:600;font-size:13px;text-transform:uppercase}
td{font-size:14px}
.action-btns{display:flex;gap:5px}
.action-btns button{padding:5px 10px;font-size:12px}
.empty{text-align:center;padding:30px;color:#999}
.msg{padding:12px;border-radius:8px;margin-bottom:15px}
.msg.ok{background:#d4edda;color:#155724}
.msg.err{background:#f8d7da;color:#721c24}

/* Ticket lists */
.ticket-row { background:#f9f9f9; padding:15px; border-radius:10px; margin-bottom:12px; border-left:4px solid #ffaa00; }
.ticket-row.answered { border-left-color: #28a745; }
.ticket-head { display:flex; justify-content:space-between; margin-bottom:8px; }
</style></head><body>
<header>
  <h1>🔐 AKEL CARGO — Панели идоракунӣ</h1>
  <div>
    <a href="/" target="_blank">🌐 Ба сайт гузаштан</a>
    <a href="/admin/logout">🚪 Баромад</a>
  </div>
</header>
<div class="container">
  {% if msg %}<div class="msg ok">{{msg}}</div>{% endif %}

  <!-- Dashboard & Profile Layout -->
  <div class="dashboard-layout">
    <!-- 1. Профили ман (Комилҷон) -->
    <div class="profile-card">
      <div class="profile-avatar">👨‍💻</div>
      <div class="profile-info">
        <h3>Комилҷон</h3>
        <span class="role">Асосгузор / Админ</span>
      </div>
      <div class="profile-details">
        <p><strong>Корхона:</strong> AKEL CARGO</p>
        <p><strong>Нархи умумӣ:</strong> 25 сомонӣ/кг</p>
        <p><strong>Минтақа:</strong> Истаравшан, 🇹🇯</p>
      </div>
    </div>

    <!-- 2. Дашборди асосӣ -->
    <div class="stats">
      <div class="stat-card"><div class="num">{{total_tracks}}</div><div class="lbl">Ҳамагӣ бор (дона)</div></div>
      <div class="stat-card"><div class="num">{{total_weight}} кг</div><div class="lbl">Вазни умумии борҳо</div></div>
      <div class="stat-card stat-card-gold"><div class="num">{{projected_revenue}} сомонӣ</div><div class="lbl">Даромади умумӣ (25с/кг)</div></div>
      <div class="stat-card"><div class="num">{{unanswered_tickets}}</div><div class="lbl">Тикетҳои беҷавоб</div></div>
    </div>
  </div>

  <!-- Опцияҳои иловаи трек -->
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:25px;">
    <!-- Иловаи Яккавор -->
    <div class="card" style="margin-bottom:0;">
      <h2>➕ Илова кардани трек-коди нав (Яккавор)</h2>
      <form method="POST" action="/admin/add">
        <div class="form-grid" style="grid-template-columns:1fr;">
          <div style="margin-bottom:10px;"><label>Трек-код</label><input type="text" name="code" placeholder="AKEL2026XXX" required></div>
          <div style="margin-bottom:10px;"><label>Номи мизоҷ</label><input type="text" name="client" placeholder="Ном Насаб"></div>
          <div style="margin-bottom:10px;"><label>Вазн (кг)</label><input type="number" name="weight" step="0.1" min="0" placeholder="5.5"></div>
          <div style="margin-bottom:10px;"><label>Зина</label>
            <select name="stage">
              <option value="0">0 — Чин</option>
              <option value="1">1 — Роҳ</option>
              <option value="2">2 — Тоҷикистон</option>
              <option value="3">3 — Омода</option>
            </select>
          </div>
          <div><button type="submit" style="width:100%;">➕ Сабти трек</button></div>
        </div>
      </form>
    </div>

    <!-- Иловаи Оммавӣ (Bulk) -->
    <div class="card" style="margin-bottom:0;">
      <h2>🚀 Иловаи оммавии трек-кодҳо (Бисёркарата)</h2>
      <p style="font-size:12px; color:#666; margin-bottom:10px;">Ҳар як трекро дар сатри нав нависед. <br>Формат: <strong>КОД, Мизоҷ, Вазн, Зина(0-3)</strong></p>
      <form method="POST" action="/admin/add_bulk">
        <div style="display:flex; flex-direction:column; gap:10px; height:100%;">
          <textarea name="bulk_data" rows="8" placeholder="Масалан:
AKEL2026005, Аҳмад, 5.4, 1
AKEL2026006, Салим, 12.0, 0
AKEL2026007" style="width:100%; padding:10px; border:2px solid #ddd; border-radius:8px; font-family:monospace; resize:none; flex:1;" required></textarea>
          <button type="submit" style="background:linear-gradient(135deg,#28a745,#218838);">⚡ Боркунии Оммавӣ</button>
        </div>
      </form>
    </div>
  </div>

  <!-- Саволҳои корбарон (Тикетҳо) -->
  <div class="card">
    <h2>📨 Паёмҳо ва Саволҳои истифодабарандагон (Тикетҳо)</h2>
    {% if tickets %}
      {% for tid, tinfo in tickets.items() %}
      <div class="ticket-row {% if tinfo.status == 'answered' %}answered{% endif %}">
        <div class="ticket-head">
          <div>
            <strong style="font-size:16px; color:#1e3c72;">👤 {{tinfo.name}}</strong> 
            <span style="font-size:13px; color:#666;">(Тамос: {{tinfo.contact}})</span>
          </div>
          <span style="font-size:12px; color:#999;">📅 {{tinfo.created_at}}</span>
        </div>
        <p style="background:#fff; padding:10px; border-radius:6px; margin-bottom:10px; color:#333;"><strong>Савол:</strong> {{tinfo.question}}</p>
        
        {% if tinfo.status == 'answered' %}
          <p style="color:#28a745; margin-bottom:10px;"><strong>Ҷавоби шумо:</strong> {{tinfo.answer}}</p>
        {% endif %}

        <!-- Кнопкаи Махсуси Ҷавоб додан ва Нест кардан -->
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <form method="POST" action="/admin/ticket/answer" style="display:flex; gap:10px; flex:1; margin-right:10px;">
            <input type="hidden" name="ticket_id" value="{{tid}}">
            <input type="text" name="answer" placeholder="Ҷавоби худро дар ин ҷо нависед..." required style="flex:1; padding:8px; border:1px solid #ddd; border-radius:6px;">
            <button type="submit" style="padding:8px 15px; font-size:13px; background:#28a745;">💬 Ҷавоб</button>
          </form>

          <form method="POST" action="/admin/ticket/delete" onsubmit="return confirm('Нест карда шавад?')">
            <input type="hidden" name="ticket_id" value="{{tid}}">
            <button type="submit" class="danger" style="padding:8px 12px; font-size:13px;">🗑️</button>
          </form>
        </div>
      </div>
      {% endfor %}
    {% else %}
      <p class="empty">Ҳоло ягон саволе ворид нашудааст.</p>
    {% endif %}
  </div>

  <!-- Рӯйхати трек-кодҳо -->
  <div class="card">
    <h2>📦 Рӯйхати ҳамаи трек-кодҳо</h2>
    {% if tracks %}
    <table>
      <thead><tr><th>Трек-код</th><th>Мизоҷ</th><th>Вазн (кг)</th><th>Зина</th><th>Навсозӣ</th><th>Амалҳо</th></tr></thead>
      <tbody>
      {% for code, info in tracks.items() %}
      <tr>
        <form method="POST" action="/admin/update" style="display:contents">
          <input type="hidden" name="code" value="{{code}}">
          <td><strong>{{code}}</strong></td>
          <td><input type="text" name="client" value="{{info.client or ''}}" style="width:140px;padding:6px;border:1px solid #ddd;border-radius:6px"></td>
          <td><input type="number" name="weight" value="{{info.weight or 0}}" step="0.1" style="width:80px;padding:6px;border:1px solid #ddd;border-radius:6px"></td>
          <td>
            <select name="stage" style="padding:6px;border:1px solid #ddd;border-radius:6px">
              {% for i, name in [(0,'Чин'),(1,'Роҳ'),(2,'Тоҷикистон'),(3,'Омода')] %}
              <option value="{{i}}" {% if info.stage == i %}selected{% endif %}>{{i}} — {{name}}</option>
              {% endfor %}
            </select>
          </td>
          <td>{{info.updated or '-'}}</td>
          <td class="action-btns">
            <button type="submit" class="warning">💾 Сабт</button>
        </form>
            <form method="POST" action="/admin/delete" style="display:inline" onsubmit="return confirm('Нест карда шавад?')">
              <input type="hidden" name="code" value="{{code}}">
              <button type="submit" class="danger">🗑️</button>
            </form>
          </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div class="empty">Ҳоло трек-код илова нашудааст</div>
    {% endif %}
  </div>
</div>
</body></html>
"""

# ============ РОУТҲО ============
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/api/track/<code>')
def api_track(code):
    tracks = load_tracks()
    code_upper = code.upper().strip()
    info = tracks.get(code_upper)
    if not info:
        return jsonify({'found': False})
    return jsonify({
        'found': True,
        'code': code_upper,
        'stage': info.get('stage', 0),
        'client': info.get('client', ''),
        'weight': info.get('weight', 0),
        'updated': info.get('updated', ''),
    })

# --- РОУТҲОИ ТИКЕТҲО (САВОЛУ ҶАВОБ) ---
@app.route('/api/ticket/add', methods=['POST'])
def api_ticket_add():
    tickets = load_tickets()
    name = request.form.get('name', '').strip()
    contact = request.form.get('contact', '').strip()
    question = request.form.get('question', '').strip()
    
    if not name or not question:
        return jsonify({'success': False, 'msg': 'Лутфан ном ва саволро пурра ворид кунед!'})
        
    tid = datetime.now().strftime('%Y%m%d%H%M%S')
    tickets[tid] = {
        'name': name,
        'contact': contact,
        'question': question,
        'answer': '',
        'status': 'unanswered',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    save_tickets(tickets)
    return jsonify({'success': True, 'msg': 'Саволи шумо қабул шуд! Навсозии саҳифаро интизор шавед.'})

@app.route('/api/tickets')
def api_tickets():
    tickets = load_tickets()
    # Фиристодани 10 тикети охирин
    sorted_tickets = sorted(tickets.items(), key=lambda x: x[0], reverse=True)[:10]
    return jsonify([{
        'id': k,
        'name': v['name'],
        'question': v['question'],
        'answer': v['answer'],
        'status': v['status'],
        'created_at': v['created_at']
    } for k, v in sorted_tickets])


# --- РОУТҲОИ АДМИН ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin'):
        return redirect(url_for('admin_panel'))
    error = None
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        error = 'Логин ё парол хато аст!'
    return render_template_string(ADMIN_LOGIN_HTML, error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/panel')
@login_required
def admin_panel():
    tracks = load_tracks()
    tickets = load_tickets()
    
    # Омор барои Дашборд
    total_tracks = len(tracks)
    total_weight = round(sum(info.get('weight', 0) for info in tracks.values()), 2)
    projected_revenue = round(total_weight * PRICE_PER_KG, 2)
    unanswered_tickets = sum(1 for t in tickets.values() if t.get('status') == 'unanswered')
    
    msg = request.args.get('msg', '')
    return render_template_string(
        ADMIN_PANEL_HTML, 
        tracks=tracks, 
        tickets=tickets,
        total_tracks=total_tracks,
        total_weight=total_weight,
        projected_revenue=projected_revenue,
        unanswered_tickets=unanswered_tickets,
        msg=msg
    )

@app.route('/admin/add', methods=['POST'])
@login_required
def admin_add():
    tracks = load_tracks()
    code = request.form.get('code', '').strip().upper()
    if not code:
        return redirect(url_for('admin_panel', msg='Хатогӣ: рамзи трек холӣ аст'))
    tracks[code] = {
        'client': request.form.get('client', '').strip(),
        'weight': float(request.form.get('weight') or 0),
        'stage': int(request.form.get('stage', 0)),
        'updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
    save_tracks(tracks)
    return redirect(url_for('admin_panel', msg=f'✅ Трек-коди {code} илова шуд'))

# Опцияи иловаи Оммавии Трек-кодҳо
@app.route('/admin/add_bulk', methods=['POST'])
@login_required
def admin_add_bulk():
    tracks = load_tracks()
    bulk_data = request.form.get('bulk_data', '').strip()
    if not bulk_data:
        return redirect(url_for('admin_panel', msg='Маълумот холӣ аст!'))
        
    lines = bulk_data.split('\n')
    added = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(',')]
        code = parts[0].upper()
        if not code:
            continue
            
        client = parts[1] if len(parts) > 1 else ""
        try:
            weight = float(parts[2]) if len(parts) > 2 else 0.0
        except ValueError:
            weight = 0.0
        try:
            stage = int(parts[3]) if len(parts) > 3 else 0
        except ValueError:
            stage = 0
            
        tracks[code] = {
            'client': client,
            'weight': weight,
            'stage': stage,
            'updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
        added += 1
        
    save_tracks(tracks)
    return redirect(url_for('admin_panel', msg=f'✅ {added} трек-кодҳо бомуваффақият бор карда шуданд!'))

@app.route('/admin/update', methods=['POST'])
@login_required
def admin_update():
    tracks = load_tracks()
    code = request.form.get('code', '').strip().upper()
    if code in tracks:
        tracks[code]['client'] = request.form.get('client', '').strip()
        tracks[code]['weight'] = float(request.form.get('weight') or 0)
        tracks[code]['stage'] = int(request.form.get('stage', 0))
        tracks[code]['updated'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        save_tracks(tracks)
    return redirect(url_for('admin_panel', msg=f'💾 Навсозӣ шуд: {code}'))

@app.route('/admin/delete', methods=['POST'])
@login_required
def admin_delete():
    tracks = load_tracks()
    code = request.form.get('code', '').strip().upper()
    if code in tracks:
        del tracks[code]
        save_tracks(tracks)
    return redirect(url_for('admin_panel', msg=f'🗑️ Нест карда шуд: {code}'))

# --- АМАЛҲОИ ТИКЕТҲО ДАР АДМИН ---
@app.route('/admin/ticket/answer', methods=['POST'])
@login_required
def admin_ticket_answer():
    tickets = load_tickets()
    tid = request.form.get('ticket_id')
    answer = request.form.get('answer', '').strip()
    if tid in tickets:
        tickets[tid]['answer'] = answer
        tickets[tid]['status'] = 'answered'
        save_tickets(tickets)
        return redirect(url_for('admin_panel', msg='✅ Ҷавоб фиристода шуд!'))
    return redirect(url_for('admin_panel', msg='❌ Хатогӣ ҳангоми ёфтани тикет'))

@app.route('/admin/ticket/delete', methods=['POST'])
@login_required
def admin_ticket_delete():
    tickets = load_tickets()
    tid = request.form.get('ticket_id')
    if tid in tickets:
        del tickets[tid]
        save_tickets(tickets)
        return redirect(url_for('admin_panel', msg='🗑️ Тикет нест карда шуд'))
    return redirect(url_for('admin_panel', msg='❌ Хатогии системавӣ'))

# ============ ОҒОЗ ============
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
