from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import json
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'akel-cargo-secret-key-2024'

# ============ ТАНЗИМОТ ============
PRICE_PER_KG = 25  # 25 сомонӣ барои 1 кг
ADMIN_USERNAME = 'Komiljon'
ADMIN_PASSWORD = 'Komiljon Orifjonzoda'
DATA_FILE = 'tracks.json'

# Зинаҳои интиқол
STAGES = ['Чин', 'Роҳ', 'Тоҷикистон', 'Омода']

# ============ ПОЙГОҲИ МАЪЛУМОТ (JSON) ============
def load_tracks():
    if not os.path.exists(DATA_FILE):
        # Трек-кодҳои намунавӣ
        default = {
            'AKEL2024001': {'stage': 1, 'client': 'Намуна 1', 'weight': 5.2, 'updated': '2026-06-20'},
            'AKELRICH001': {'stage': 2, 'client': 'Намуна 2', 'weight': 12.5, 'updated': '2026-06-21'},
            'AKEL2024999': {'stage': 3, 'client': 'Намуна 3', 'weight': 8.0, 'updated': '2026-06-22'},
        }
        save_tracks(default)
        return default
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_tracks(tracks):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(tracks, f, ensure_ascii=False, indent=2)

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
.track-form input { flex:1; min-width:250px; padding:14px 18px; border:2px solid #ddd; border-radius:10px; font-size:16px; outline:none; transition:border 0.3s; }
.track-form input:focus { border-color:#1e3c72; }
.btn { background:linear-gradient(135deg,#1e3c72,#2a5298); color:#fff; border:none; padding:14px 30px; border-radius:10px; font-size:16px; font-weight:600; cursor:pointer; transition:all 0.3s; }
.btn:hover { transform:translateY(-2px); box-shadow:0 5px 15px rgba(30,60,114,0.4); }
.btn-gold { background:linear-gradient(135deg,#ffd700,#ffaa00); color:#1e3c72; }

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
    <a href="#faq">❓ Саволу ҷавоб</a>
    <a href="#contact">📞 Тамос</a>
  </nav>

  <div class="card" id="track">
    <h2>🔍 Санҷиши трек-код</h2>
    <p style="color:#666;margin-bottom:15px">Трек-кодатонро ворид кунед то ҷойгиршавии бори худро бубинед</p>
    <div class="track-form">
      <input type="text" id="trackInput" placeholder="Масалан: AKEL2024001" autocomplete="off">
      <button class="btn" onclick="searchTrack()">Ҷустуҷӯ</button>
    </div>
    <div id="trackResult"></div>
  </div>

  <div class="card" id="calc">
    <h2>💰 Калкулятори нарх</h2>
    <p style="color:#666;margin-bottom:15px">Нархи 1 кг — <strong style="color:#1e3c72">27 сомонӣ</strong></p>
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

  <div class="card" id="faq">
    <h2>❓ Саволу ҷавоб</h2>
    <div class="faq-item">
      <div class="faq-question" onclick="toggleFaq(this)">Бор чанд рӯз меояд?<span class="arrow">▼</span></div>
      <div class="faq-answer">Одатан 15-25 рӯз. Аз Чин ба Тоҷикистон вобаста ба мавсим ва намуди бор.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question" onclick="toggleFaq(this)">Чӣ тавр трек-код мегирам?<span class="arrow">▼</span></div>
      <div class="faq-answer">Пас аз он ки бори шумо ба анбори мо мерасад, мо ба воситаи Telegram ё телефон ба шумо трек-код медиҳем.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question" onclick="toggleFaq(this)">Нархи интиқол чанд аст?<span class="arrow">▼</span></div>
      <div class="faq-answer">25 сомонӣ барои 1 кг. Барои борҳои калон тахфиф пешбинӣ шудааст. Калкулятори моро истифода баред.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question" onclick="toggleFaq(this)">Чӣ намуди борҳоро қабул мекунед?<span class="arrow">▼</span></div>
      <div class="faq-answer">Либос, техника, телефон, лавозимоти хона, маҳсулоти зебоӣ ва ғайра. Маводи мамнӯъ (зарарнок, маводи мухаддир) қабул намешавад.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question" onclick="toggleFaq(this)">Агар бор гум шавад чӣ кор кунам?<span class="arrow">▼</span></div>
      <div class="faq-answer">Мо барои ҳар як бор кафолат дорем. Дар ҳолати гум шудан мо арзиши онро баргардонида медиҳем. Бо мо ба тамос шавед.</div>
    </div>
  </div>

  <div class="card" id="contact">
    <h2>📞 Бо мо тамос гиред</h2>
    <div class="contact-grid">
      <a href="https://t.me/AKELRICH5000" class="contact-card" target="_blank">
        <div class="icon">✈️</div>
        <div class="label">Telegram</div>
        <div class="value">@AKELRICH5000</div>
      </a>
      <a href="tel:+992715555000" class="contact-card">
        <div class="icon">📞</div>
        <div class="label">Телефон</div>
        <div class="value">+992 71 555 50 00</div>
      </a>
      <a href="https://wa.me/992715555000" class="contact-card" target="_blank">
        <div class="icon">💬</div>
        <div class="label">WhatsApp</div>
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
    <p>© 2024 AKEL CARGO. Ҳамаи ҳуқуқҳо ҳифз карда шудаанд.</p>
    <p>Карго аз Чин ба Тоҷикистон • <a href="#track">Бозгашт ба боло</a></p>
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
  const stage = data.stage; // 0-3
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
  // animate progress
  setTimeout(() => {
    const progress = (stage / (STAGES.length - 1)) * 100;
    document.getElementById('tlProgress').style.width = progress + '%';
  }, 100);
}

function calculate(){
  const w = parseFloat(document.getElementById('calcWeight').value) || 0;
  const q = parseInt(document.getElementById('calcQty').value) || 1;
  const total = w * q * 27;
  document.getElementById('calcPrice').textContent = total.toFixed(2) + ' сомонӣ';
  if(w > 0){
    document.getElementById('calcDetail').textContent = `${w} кг × ${q} баста × 27 сомонӣ`;
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
  <input type="text" name="username" placeholder="Логин" required autofocus>
  <input type="password" name="password" placeholder="Парол" required>
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
.card{background:#fff;border-radius:15px;padding:25px;margin-bottom:20px;box-shadow:0 4px 15px rgba(0,0,0,0.08)}
.card h2{color:#1e3c72;margin-bottom:20px;font-size:20px}
.form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;align-items:end}
.form-grid label{font-size:13px;color:#555;font-weight:600;display:block;margin-bottom:5px}
.form-grid input,.form-grid select{width:100%;padding:10px;border:2px solid #ddd;border-radius:8px;font-size:14px}
.form-grid input:focus,.form-grid select:focus{outline:none;border-color:#1e3c72}
button{background:linear-gradient(135deg,#1e3c72,#2a5298);color:#fff;border:none;padding:10px 20px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;transition:all 0.3s}
button:hover{transform:translateY(-2px);box-shadow:0 5px 15px rgba(30,60,114,0.3)}
button.danger{background:linear-gradient(135deg,#d9534f,#c9302c)}
button.warning{background:linear-gradient(135deg,#f0ad4e,#ec971f)}
table{width:100%;border-collapse:collapse;margin-top:15px}
th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}
th{background:#f8f9fa;color:#1e3c72;font-weight:600;font-size:13px;text-transform:uppercase}
td{font-size:14px}
.stage-badge{padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600;display:inline-block}
.stage-0{background:#fff3cd;color:#856404}
.stage-1{background:#cce5ff;color:#004085}
.stage-2{background:#d4edda;color:#155724}
.stage-3{background:#d1ecf1;color:#0c5460}
.action-btns{display:flex;gap:5px}
.action-btns button{padding:5px 10px;font-size:12px}
.empty{text-align:center;padding:30px;color:#999}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:20px}
.stat-card{background:linear-gradient(135deg,#1e3c72,#2a5298);color:#fff;padding:20px;border-radius:15px}
.stat-card .num{font-size:36px;font-weight:900;color:#ffd700}
.stat-card .lbl{font-size:13px;opacity:0.9;margin-top:5px}
.msg{padding:12px;border-radius:8px;margin-bottom:15px}
.msg.ok{background:#d4edda;color:#155724}
.msg.err{background:#f8d7da;color:#721c24}
</style></head><body>
<header>
  <h1>🔐 AKEL CARGO — Панели идоракунӣ</h1>
  <div>
    <a href="/" target="_blank">🌐 Сайт</a>
    <a href="/admin/logout">🚪 Баромад</a>
  </div>
</header>
<div class="container">
  {% if msg %}<div class="msg ok">{{msg}}</div>{% endif %}

  <div class="stats">
    <div class="stat-card"><div class="num">{{total}}</div><div class="lbl">Ҳамагӣ бор</div></div>
    <div class="stat-card"><div class="num">{{counts[0]}}</div><div class="lbl">Дар Чин</div></div>
    <div class="stat-card"><div class="num">{{counts[1]}}</div><div class="lbl">Дар роҳ</div></div>
    <div class="stat-card"><div class="num">{{counts[2] + counts[3]}}</div><div class="lbl">Дар Тоҷикистон</div></div>
  </div>

  <div class="card">
    <h2>➕ Илова кардани трек-коди нав</h2>
    <form method="POST" action="/admin/add">
      <div class="form-grid">
        <div><label>Трек-код</label><input type="text" name="code" placeholder="AKEL2024XXX" required></div>
        <div><label>Номи мизоҷ</label><input type="text" name="client" placeholder="Ном Насаб"></div>
        <div><label>Вазн (кг)</label><input type="number" name="weight" step="0.1" min="0" placeholder="5.5"></div>
        <div><label>Зина</label>
          <select name="stage">
            <option value="0">0 — Чин</option>
            <option value="1">1 — Роҳ</option>
            <option value="2">2 — Тоҷикистон</option>
            <option value="3">3 — Омода</option>
          </select>
        </div>
        <div><button type="submit">➕ Илова кардан</button></div>
      </div>
    </form>
  </div>

  <div class="card">
    <h2>📦 Рӯйхати трек-кодҳо</h2>
    {% if tracks %}
    <table>
      <thead><tr><th>Трек-код</th><th>Мизоҷ</th><th>Вазн</th><th>Зина</th><th>Навсозӣ</th><th>Амалҳо</th></tr></thead>
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
        error = 'Логин ё парол нодуруст аст'
    return render_template_string(ADMIN_LOGIN_HTML, error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/panel')
@login_required
def admin_panel():
    tracks = load_tracks()
    counts = [0, 0, 0, 0]
    for info in tracks.values():
        s = info.get('stage', 0)
        if 0 <= s <= 3:
            counts[s] += 1
    msg = request.args.get('msg', '')
    return render_template_string(ADMIN_PANEL_HTML, tracks=tracks, total=len(tracks), counts=counts, msg=msg)

@app.route('/admin/add', methods=['POST'])
@login_required
def admin_add():
    tracks = load_tracks()
    code = request.form.get('code', '').strip().upper()
    if not code:
        return redirect(url_for('admin_panel', msg='Трек-код холӣ аст'))
    tracks[code] = {
        'client': request.form.get('client', '').strip(),
        'weight': float(request.form.get('weight') or 0),
        'stage': int(request.form.get('stage', 0)),
        'updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
    save_tracks(tracks)
    return redirect(url_for('admin_panel', msg=f'✅ Трек-код {code} илова шуд'))

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
    return redirect(url_for('admin_panel', msg=f'💾 {code} навсозӣ шуд'))

@app.route('/admin/delete', methods=['POST'])
@login_required
def admin_delete():
    tracks = load_tracks()
    code = request.form.get('code', '').strip().upper()
    if code in tracks:
        del tracks[code]
        save_tracks(tracks)
    return redirect(url_for('admin_panel', msg=f'🗑️ {code} нест карда шуд'))

# ============ ОҒОЗ (Ислоҳшуда барои Railway) ============
if __name__ == '__main__':
    # Railway ба таври худкор тағирёбандаи PORT-ро ба мо медиҳад.
    # Мо бояд онро муайян кунем, то барнома хатогӣ (Error) надиҳад.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
