"""
TAJWAY CARGO - Сомонаи интернетӣ барои идоракунии карго
Иҷро: Flask
Корхона: TAJWAY CARGO
Нарх: 27 сомонӣ/кг
Забон: Тоҷикӣ / Русский

Истифода:
    pip install flask
    python cargoakel.py
    Кушоиш: http://localhost:5000

Панели админ: http://localhost:5000/admin
    Логин: admin
    Парол: tajway2024
"""

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import json
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'tajway-cargo-secret-key-2024'

# ============ ТАНЗИМОТ ============
PRICE_PER_KG = 27  # 27 сомонӣ барои 1 кг
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'tajway2024'
DATA_FILE = 'tracks.json'

# Зинаҳои интиқол
STAGES = ['Чин', 'Роҳ', 'Тоҷикистон', 'Омода']

# ============ ПОЙГОҲИ МАЪЛУМОТ (JSON) ============
def load_tracks():
    if not os.path.exists(DATA_FILE):
        # Трек-кодҳои намунавӣ
        default = {
            'TAJWAY2024001': {'stage': 1, 'client': 'Намуна 1', 'weight': 5.2, 'updated': '2026-06-20'},
            'TAJWAYRICH001': {'stage': 2, 'client': 'Намуна 2', 'weight': 12.5, 'updated': '2026-06-21'},
            'TAJWAY2024999': {'stage': 3, 'client': 'Намуна 3', 'weight': 8.0, 'updated': '2026-06-22'},
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
<title>TAJWAY CARGO — Карго аз Чин ба Тоҷикистон</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
body { background: #0f172a; min-height:100vh; color:#fff; overflow-x:hidden; }
.container { max-width:1200px; margin:0 auto; padding:20px; }

/* Animated background */
.bg-anim { position:fixed; top:0; left:0; width:100%; height:100%; z-index:-1; overflow:hidden; }
.bg-anim .circle { position:absolute; border-radius:50%; filter:blur(80px); opacity:0.4; animation:float 20s infinite ease-in-out; }
.bg-anim .c1 { width:400px; height:400px; background:linear-gradient(135deg,#6366f1,#8b5cf6); top:-100px; left:-100px; animation-delay:0s; }
.bg-anim .c2 { width:500px; height:500px; background:linear-gradient(135deg,#ec4899,#f43f5e); bottom:-150px; right:-100px; animation-delay:-5s; }
.bg-anim .c3 { width:300px; height:300px; background:linear-gradient(135deg,#06b6d4,#3b82f6); top:40%; left:60%; animation-delay:-10s; }
@keyframes float { 0%,100%{transform:translate(0,0) scale(1);} 33%{transform:translate(30px,-30px) scale(1.1);} 66%{transform:translate(-20px,20px) scale(0.9);} }

/* Header */
header { text-align:center; padding:60px 0 40px; position:relative; }
header .badge { display:inline-block; background:rgba(255,255,255,0.1); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.2); padding:8px 20px; border-radius:50px; font-size:13px; letter-spacing:2px; text-transform:uppercase; margin-bottom:20px; color:#cbd5e1; }
header h1 { font-size:64px; font-weight:900; letter-spacing:4px; text-shadow:0 0 40px rgba(99,102,241,0.5); line-height:1.1; }
header h1 .logo-accent { background:linear-gradient(135deg,#6366f1,#ec4899); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
header p { font-size:20px; margin-top:15px; opacity:0.8; color:#94a3b8; max-width:600px; margin-left:auto; margin-right:auto; }
header .stats-row { display:flex; justify-content:center; gap:40px; margin-top:30px; flex-wrap:wrap; }
header .stat { text-align:center; }
header .stat .num { font-size:32px; font-weight:800; color:#6366f1; }
header .stat .lbl { font-size:12px; text-transform:uppercase; letter-spacing:1px; color:#64748b; margin-top:4px; }

/* Nav */
nav { display:flex; justify-content:center; gap:12px; flex-wrap:wrap; margin:30px 0 40px; position:sticky; top:10px; z-index:100; }
nav a { background:rgba(255,255,255,0.08); backdrop-filter:blur(20px); border:1px solid rgba(255,255,255,0.1); color:#e2e8f0; padding:12px 24px; border-radius:50px; text-decoration:none; transition:all 0.3s; font-size:14px; font-weight:500; }
nav a:hover { background:rgba(99,102,241,0.2); border-color:rgba(99,102,241,0.4); transform:translateY(-2px); box-shadow:0 10px 30px rgba(99,102,241,0.2); }

/* Cards */
.card { background:rgba(255,255,255,0.03); backdrop-filter:blur(20px); border:1px solid rgba(255,255,255,0.08); border-radius:24px; padding:40px; margin-bottom:30px; box-shadow:0 20px 60px rgba(0,0,0,0.3); transition:all 0.3s; }
.card:hover { border-color:rgba(99,102,241,0.2); transform:translateY(-2px); }
.card h2 { color:#fff; margin-bottom:20px; font-size:28px; display:flex; align-items:center; gap:12px; font-weight:700; }
.card h2 .icon-bg { width:44px; height:44px; border-radius:12px; background:linear-gradient(135deg,#6366f1,#8b5cf6); display:flex; align-items:center; justify-content:center; font-size:22px; }
.card p { color:#94a3b8; margin-bottom:20px; line-height:1.6; }

/* Track Search */
.track-form { display:flex; gap:12px; flex-wrap:wrap; }
.track-form input { flex:1; min-width:280px; padding:16px 22px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:14px; font-size:16px; outline:none; transition:all 0.3s; color:#fff; }
.track-form input::placeholder { color:#64748b; }
.track-form input:focus { border-color:#6366f1; background:rgba(99,102,241,0.05); box-shadow:0 0 20px rgba(99,102,241,0.1); }
.btn { background:linear-gradient(135deg,#6366f1,#8b5cf6); color:#fff; border:none; padding:16px 36px; border-radius:14px; font-size:16px; font-weight:600; cursor:pointer; transition:all 0.3s; position:relative; overflow:hidden; }
.btn::before { content:''; position:absolute; top:0; left:-100%; width:100%; height:100%; background:linear-gradient(90deg,transparent,rgba(255,255,255,0.2),transparent); transition:0.5s; }
.btn:hover::before { left:100%; }
.btn:hover { transform:translateY(-2px); box-shadow:0 10px 30px rgba(99,102,241,0.4); }
.btn-gold { background:linear-gradient(135deg,#f59e0b,#fbbf24); color:#0f172a; }

/* Timeline */
.timeline { display:flex; justify-content:space-between; align-items:center; margin:50px 0 25px; position:relative; padding:0 30px; }
.timeline::before { content:''; position:absolute; top:35px; left:80px; right:80px; height:3px; background:rgba(255,255,255,0.1); z-index:0; border-radius:3px; }
.timeline-progress { position:absolute; top:35px; left:80px; height:3px; background:linear-gradient(90deg,#6366f1,#ec4899); z-index:1; width:0%; transition:width 1.5s ease; border-radius:3px; }
.stage { position:relative; z-index:2; text-align:center; flex:1; }
.stage-circle { width:70px; height:70px; border-radius:50%; background:rgba(255,255,255,0.05); border:2px solid rgba(255,255,255,0.1); color:#64748b; margin:0 auto 12px; display:flex; align-items:center; justify-content:center; font-size:28px; font-weight:bold; transition:all 0.5s; position:relative; }
.stage.active .stage-circle { background:linear-gradient(135deg,#6366f1,#8b5cf6); color:#fff; border-color:transparent; transform:scale(1.1); box-shadow:0 0 30px rgba(99,102,241,0.4); }
.stage.current .stage-circle { animation:pulse 2s infinite; box-shadow:0 0 40px rgba(236,72,153,0.5); }
@keyframes pulse { 0%,100%{box-shadow:0 0 0 0 rgba(236,72,153,0.4);} 50%{box-shadow:0 0 0 20px rgba(236,72,153,0);} }
.stage-label { font-size:13px; font-weight:600; color:#64748b; transition:color 0.3s; }
.stage.active .stage-label { color:#e2e8f0; }
.stage.current .stage-label { color:#ec4899; }

.result-info { background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.2); padding:20px; border-radius:16px; margin-top:25px; }
.result-info p { margin:8px 0; color:#cbd5e1; }
.result-info p strong { color:#6366f1; }
.result-error { background:rgba(244,63,94,0.1); border:1px solid rgba(244,63,94,0.2); padding:20px; border-radius:16px; margin-top:25px; color:#f43f5e; }

/* Calculator */
.calc-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:20px; }
.calc-grid label { display:block; font-weight:600; color:#e2e8f0; margin-bottom:10px; font-size:14px; }
.calc-grid input { width:100%; padding:14px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:12px; font-size:16px; outline:none; color:#fff; transition:all 0.3s; }
.calc-grid input:focus { border-color:#6366f1; }
.calc-grid input::placeholder { color:#64748b; }
.calc-result { background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(236,72,153,0.15)); border:1px solid rgba(99,102,241,0.2); padding:30px; border-radius:20px; text-align:center; margin-top:25px; }
.calc-result .price { font-size:48px; font-weight:900; background:linear-gradient(135deg,#6366f1,#ec4899); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; margin:10px 0; }
.calc-result .detail { font-size:14px; color:#94a3b8; }

/* Address */
.address-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
.address-box { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:25px; transition:all 0.3s; }
.address-box:hover { border-color:rgba(99,102,241,0.3); }
.address-box h3 { color:#fff; margin-bottom:12px; display:flex; align-items:center; gap:10px; font-size:18px; }
.address-text { background:rgba(0,0,0,0.2); padding:14px; border-radius:10px; font-family:'Courier New',monospace; word-break:break-all; margin-bottom:12px; color:#cbd5e1; font-size:13px; line-height:1.6; border:1px solid rgba(255,255,255,0.05); }
.copy-btn { background:rgba(99,102,241,0.15); color:#6366f1; border:1px solid rgba(99,102,241,0.3); padding:10px 18px; border-radius:10px; cursor:pointer; font-size:14px; font-weight:500; transition:all 0.3s; }
.copy-btn:hover { background:rgba(99,102,241,0.3); color:#fff; }
.copy-btn.copied { background:rgba(34,197,94,0.2); color:#22c55e; border-color:rgba(34,197,94,0.4); }

/* FAQ */
.faq-item { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:14px; margin-bottom:12px; overflow:hidden; transition:all 0.3s; }
.faq-item:hover { border-color:rgba(99,102,241,0.2); }
.faq-question { padding:18px 24px; cursor:pointer; font-weight:600; color:#e2e8f0; display:flex; justify-content:space-between; align-items:center; user-select:none; font-size:15px; }
.faq-question:hover { background:rgba(99,102,241,0.05); }
.faq-answer { padding:0 24px; max-height:0; overflow:hidden; transition:all 0.4s ease; color:#94a3b8; line-height:1.7; }
.faq-item.active .faq-answer { padding:0 24px 20px; max-height:300px; }
.faq-item.active .faq-question .arrow { transform:rotate(180deg); color:#6366f1; }
.arrow { transition:transform 0.3s; color:#64748b; }

/* Contact */
.contact-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; }
.contact-card { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); padding:25px; border-radius:16px; text-align:center; text-decoration:none; color:#e2e8f0; transition:all 0.3s; }
.contact-card:hover { transform:translateY(-4px); border-color:rgba(99,102,241,0.3); box-shadow:0 15px 40px rgba(99,102,241,0.15); }
.contact-card .icon { font-size:40px; margin-bottom:12px; }
.contact-card .label { font-weight:600; font-size:16px; }
.contact-card .value { font-size:13px; color:#64748b; margin-top:6px; }

/* Prohibited Items */
.prohibited { background:linear-gradient(135deg,rgba(244,63,94,0.1),rgba(251,191,36,0.1)); border:1px solid rgba(244,63,94,0.2); border-radius:20px; padding:30px; }
.prohibited h3 { color:#f43f5e; font-size:20px; margin-bottom:20px; display:flex; align-items:center; gap:10px; }
.prohibited-list { display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:12px; }
.prohibited-item { display:flex; align-items:center; gap:12px; background:rgba(0,0,0,0.2); padding:14px 18px; border-radius:12px; border:1px solid rgba(244,63,94,0.1); }
.prohibited-item .x { font-size:20px; color:#f43f5e; font-weight:bold; flex-shrink:0; }
.prohibited-item span { color:#cbd5e1; font-size:14px; }
.prohibited-footer { margin-top:20px; padding-top:20px; border-top:1px solid rgba(244,63,94,0.1); color:#94a3b8; font-size:14px; line-height:1.6; }
.prohibited-footer strong { color:#fbbf24; }

/* Footer */
footer { text-align:center; padding:50px 0 30px; }
footer .logo { font-size:24px; font-weight:800; letter-spacing:3px; margin-bottom:10px; }
footer .logo span { background:linear-gradient(135deg,#6366f1,#ec4899); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
footer p { color:#64748b; font-size:14px; }
footer a { color:#6366f1; text-decoration:none; }

/* Scrollbar */
::-webkit-scrollbar { width:8px; }
::-webkit-scrollbar-track { background:#0f172a; }
::-webkit-scrollbar-thumb { background:#334155; border-radius:4px; }
::-webkit-scrollbar-thumb:hover { background:#475569; }

@media(max-width:768px){
  header h1{font-size:36px;}
  .calc-grid{grid-template-columns:1fr;}
  .address-grid{grid-template-columns:1fr;}
  .timeline-progress{left:50px;}
  .timeline::before{left:50px;right:50px;}
  .timeline{padding:0 10px;}
  .stage-circle{width:50px;height:50px;font-size:20px;}
  .stage-label{font-size:11px;}
  .card{padding:25px;}
  header .stats-row{gap:20px;}
}
</style>
</head>
<body>
<div class="bg-anim"><div class="circle c1"></div><div class="circle c2"></div><div class="circle c3"></div></div>

<div class="container">
  <header>
    <div class="badge">🚚 Карго аз Чин ба Тоҷикистон</div>
    <h1>TAJWAY <span class="logo-accent">CARGO</span></h1>
    <p>Зуд, бехатар, бо кафолат. Борҳои шуморо аз Чин ба Тоҷикистон мерасонем.</p>
    <div class="stats-row">
      <div class="stat"><div class="num">15-25</div><div class="lbl">Рӯз интиқол</div></div>
      <div class="stat"><div class="num">27</div><div class="lbl">Сомонӣ/кг</div></div>
      <div class="stat"><div class="num">100%</div><div class="lbl">Кафолат</div></div>
    </div>
  </header>

  <nav>
    <a href="#track">🔍 Санҷиши трек</a>
    <a href="#calc">💰 Калкулятор</a>
    <a href="#address">📍 Адрес</a>
    <a href="#prohibited">⚠️ Манъшуда</a>
    <a href="#faq">❓ Саволу ҷавоб</a>
    <a href="#contact">📞 Тамос</a>
  </nav>

  <!-- Track Search -->
  <div class="card" id="track">
    <h2><span class="icon-bg">🔍</span> Санҷиши трек-код</h2>
    <p>Трек-кодатонро ворид кунед то ҷойгиршавии бори худро бубинед</p>
    <div class="track-form">
      <input type="text" id="trackInput" placeholder="Масалан: TAJWAY2024001" autocomplete="off">
      <button class="btn" onclick="searchTrack()">Ҷустуҷӯ</button>
    </div>
    <div id="trackResult"></div>
  </div>

  <!-- Calculator -->
  <div class="card" id="calc">
    <h2><span class="icon-bg">💰</span> Калкулятори нарх</h2>
    <p>Нархи 1 кг — <strong style="color:#6366f1">27 сомонӣ</strong>. Вазн ва миқдорро ворид кунед.</p>
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

  <!-- Address -->
  <div class="card" id="address">
    <h2><span class="icon-bg">📍</span> Адреси анбор</h2>
    <div class="address-grid">
      <div class="address-box">
        <h3>🇨🇳 Анбор дар Чин</h3>
        <div class="address-text" id="addrChina">KHMIR 15625450102
浙江省金华市义乌市 商城大道与柳青路交叉口东北220米洪华小区102栋2单元一楼
(MIR nom tel)</div>
        <button class="copy-btn" onclick="copyText('addrChina', this)">📋 Нусхабардорӣ</button>
      </div>
      <div class="address-box">
        <h3>🇹🇯 Анбор дар Тоҷикистон (Истаравшан)</h3>
        <div class="address-text" id="addrTj">ш. Истаравшан, TAJWAY CARGO
кӯчаи марказӣ, наздикии бозори марказӣ
Тел: +992 71 555 50 00</div>
        <button class="copy-btn" onclick="copyText('addrTj', this)">📋 Нусхабардорӣ</button>
      </div>
    </div>
  </div>

  <!-- Prohibited Items -->
  <div class="card" id="prohibited">
    <div class="prohibited">
      <h3>⚠️ ВНИМАНИЕ! Запрещённые товары при доставке из Китая</h3>
      <p style="color:#94a3b8;margin-bottom:20px">Друзья, сейчас проверки особенно строгие. Чтобы избежать проблем с отправкой, просим не заказывать:</p>
      <div class="prohibited-list">
        <div class="prohibited-item"><span class="x">❌</span><span>Лекарства (таблетки, порошки, жидкости)</span></div>
        <div class="prohibited-item"><span class="x">❌</span><span>Оружие и электрошокеры</span></div>
        <div class="prohibited-item"><span class="x">❌</span><span>Электронные сигареты, кальяны и аксессуары</span></div>
        <div class="prohibited-item"><span class="x">❌</span><span>Товары 18+</span></div>
        <div class="prohibited-item"><span class="x">❌</span><span>Смартфоны и телефоны</span></div>
        <div class="prohibited-item"><span class="x">❌</span><span>Повербанки</span></div>
      </div>
      <div class="prohibited-footer">
        <strong>‼️ Эти товары мы не принимаем и не отправляем.</strong><br><br>
        Спасибо за понимание и соблюдение правил 🙏<br>
        С уважением, Команда <strong>TAJWAY CARGO</strong>
      </div>
    </div>
  </div>

  <!-- FAQ -->
  <div class="card" id="faq">
    <h2><span class="icon-bg">❓</span> Саволу ҷавоб</h2>
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
      <div class="faq-answer">27 сомонӣ барои 1 кг. Барои борҳои калон тахфиф пешбинӣ шудааст. Калкулятори моро истифода баред.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question" onclick="toggleFaq(this)">Чӣ намуди борҳоро қабул мекунед?<span class="arrow">▼</span></div>
      <div class="faq-answer">Либос, техника, лавозимоти хона, маҳсулоти зебоӣ ва ғайра. Маводи мамнӯъ (зарарнок, маводи мухаддир) қабул намешавад. Рӯйхати пурра дар бахши "Манъшуда".</div>
    </div>
    <div class="faq-item">
      <div class="faq-question" onclick="toggleFaq(this)">Агар бор гум шавад чӣ кор кунам?<span class="arrow">▼</span></div>
      <div class="faq-answer">Мо барои ҳар як бор кафолат дорем. Дар ҳолати гум шудан мо арзиши онро баргардонида медиҳем. Бо мо ба тамос шавед.</div>
    </div>
  </div>

  <!-- Contact -->
  <div class="card" id="contact">
    <h2><span class="icon-bg">📞</span> Бо мо тамос гиред</h2>
    <div class="contact-grid">
      <a href="https://t.me/TAJWAYCARGO" class="contact-card" target="_blank">
        <div class="icon">✈️</div>
        <div class="label">Telegram</div>
        <div class="value">@TAJWAYCARGO</div>
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
    <div class="logo">TAJWAY <span>CARGO</span></div>
    <p>© 2024 TAJWAY CARGO. Ҳамаи ҳуқуқҳо ҳифз карда шудаанд. Карго аз Чин ба Тоҷикистон.</p>
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
  resultDiv.innerHTML = '<div style="text-align:center;padding:30px;color:#64748b"><div style="font-size:40px;margin-bottom:10px">⏳</div>Ҷустуҷӯ...</div>';
  try {
    const res = await fetch('/api/track/' + encodeURIComponent(code));
    const data = await res.json();
    if(!data.found){
      resultDiv.innerHTML = '<div class="result-error"><div style="font-size:40px;margin-bottom:10px">❌</div>Трек-код ёфт нашуд. Лутфан санҷед ё бо мо тамос гиред.</div>';
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

// Smooth scroll for nav links
document.querySelectorAll('nav a').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    const target = document.querySelector(a.getAttribute('href'));
    if(target) target.scrollIntoView({behavior:'smooth', block:'start'});
  });
});
</script>
</body>
</html>
"""

# ============ САҲИФАИ АДМИН ============
ADMIN_LOGIN_HTML = r"""<!DOCTYPE html>
<html lang="tg"><head><meta charset="UTF-8"><title>Воридшавӣ — TAJWAY CARGO Admin</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Segoe UI,sans-serif}
body{background:#0f172a;min-height:100vh;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden}
body::before{content:'';position:absolute;width:500px;height:500px;background:linear-gradient(135deg,#6366f1,#ec4899);border-radius:50%;filter:blur(120px);opacity:0.3;top:-200px;left:-200px}
body::after{content:'';position:absolute;width:400px;height:400px;background:linear-gradient(135deg,#06b6d4,#3b82f6);border-radius:50%;filter:blur(120px);opacity:0.2;bottom:-150px;right:-150px}
.box{background:rgba(255,255,255,0.03);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.08);padding:50px;border-radius:24px;box-shadow:0 20px 60px rgba(0,0,0,0.3);width:90%;max-width:420px;position:relative;z-index:1}
h1{color:#fff;text-align:center;margin-bottom:30px;font-size:28px;font-weight:700}
h1 span{background:linear-gradient(135deg,#6366f1,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
input{width:100%;padding:16px;margin-bottom:15px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:14px;font-size:16px;box-sizing:border-box;color:#fff;outline:none;transition:all 0.3s}
input::placeholder{color:#64748b}
input:focus{border-color:#6366f1;box-shadow:0 0 20px rgba(99,102,241,0.1)}
button{width:100%;padding:16px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none;border-radius:14px;font-size:16px;font-weight:600;cursor:pointer;transition:all 0.3s}
button:hover{transform:translateY(-2px);box-shadow:0 10px 30px rgba(99,102,241,0.4)}
.error{background:rgba(244,63,94,0.1);color:#f43f5e;padding:12px;border-radius:10px;margin-bottom:15px;text-align:center;border:1px solid rgba(244,63,94,0.2)}
.back{display:block;text-align:center;margin-top:20px;color:#64748b;text-decoration:none;transition:color 0.3s}
.back:hover{color:#6366f1}
</style></head><body>
<form class="box" method="POST">
  <h1>🔐 TAJWAY <span>CARGO</span> Admin</h1>
  {% if error %}<div class="error">{{error}}</div>{% endif %}
  <input type="text" name="username" placeholder="Логин" required autofocus>
  <input type="password" name="password" placeholder="Парол" required>
  <button type="submit">Воридшавӣ</button>
  <a href="/" class="back">← Бозгашт ба сайт</a>
</form></body></html>
"""

ADMIN_PANEL_HTML = r"""<!DOCTYPE html>
<html lang="tg"><head><meta charset="UTF-8"><title>Панели идоракунӣ — TAJWAY CARGO</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Segoe UI,sans-serif}
body{background:#0f172a;min-height:100vh;color:#e2e8f0}
header{background:rgba(255,255,255,0.03);backdrop-filter:blur(20px);border-bottom:1px solid rgba(255,255,255,0.08);color:#fff;padding:20px 30px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100}
header h1{font-size:22px;font-weight:700}
header h1 span{background:linear-gradient(135deg,#6366f1,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
header a{color:#64748b;text-decoration:none;padding:10px 18px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;transition:all 0.3s;margin-left:8px;font-size:13px}
header a:hover{color:#6366f1;border-color:rgba(99,102,241,0.3)}
.container{max-width:1200px;margin:30px auto;padding:0 20px}
.card{background:rgba(255,255,255,0.03);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:30px;margin-bottom:25px;box-shadow:0 10px 40px rgba(0,0,0,0.2)}
.card h2{color:#fff;margin-bottom:20px;font-size:20px;font-weight:600}
.form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;align-items:end}
.form-grid label{font-size:13px;color:#94a3b8;font-weight:600;display:block;margin-bottom:8px}
.form-grid input,.form-grid select{width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;font-size:14px;color:#fff;outline:none;transition:all 0.3s}
.form-grid input:focus,.form-grid select:focus{border-color:#6366f1}
.form-grid input::placeholder{color:#64748b}
button{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none;padding:12px 24px;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;transition:all 0.3s}
button:hover{transform:translateY(-2px);box-shadow:0 8px 25px rgba(99,102,241,0.3)}
button.danger{background:linear-gradient(135deg,#f43f5e,#e11d48)}
button.warning{background:linear-gradient(135deg,#f59e0b,#fbbf24);color:#0f172a}
table{width:100%;border-collapse:collapse;margin-top:15px}
th,td{padding:14px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.05)}
th{background:rgba(255,255,255,0.03);color:#94a3b8;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:1px}
td{font-size:14px;color:#cbd5e1}
.stage-badge{padding:6px 12px;border-radius:20px;font-size:12px;font-weight:600;display:inline-block}
.stage-0{background:rgba(251,191,36,0.15);color:#fbbf24}
.stage-1{background:rgba(59,130,246,0.15);color:#60a5fa}
.stage-2{background:rgba(34,197,94,0.15);color:#22c55e}
.stage-3{background:rgba(99,102,241,0.15);color:#818cf8}
.action-btns{display:flex;gap:6px}
.action-btns button{padding:6px 12px;font-size:12px}
.empty{text-align:center;padding:40px;color:#64748b}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:25px}
.stat-card{background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(236,72,153,0.1));border:1px solid rgba(99,102,241,0.2);padding:25px;border-radius:16px}
.stat-card .num{font-size:36px;font-weight:900;background:linear-gradient(135deg,#6366f1,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.stat-card .lbl{font-size:13px;color:#94a3b8;margin-top:6px}
.msg{padding:14px;border-radius:12px;margin-bottom:20px;font-size:14px}
.msg.ok{background:rgba(34,197,94,0.1);color:#22c55e;border:1px solid rgba(34,197,94,0.2)}
.msg.err{background:rgba(244,63,94,0.1);color:#f43f5e;border:1px solid rgba(244,63,94,0.2)}
input[type="text"],input[type="number"]{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:8px 10px;color:#fff;font-size:13px;outline:none}
input[type="text"]:focus,input[type="number"]:focus{border-color:#6366f1}
select{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:8px 10px;color:#fff;font-size:13px;outline:none}
</style></head><body>
<header>
  <h1>🔐 TAJWAY <span>CARGO</span> — Панели идоракунӣ</h1>
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
        <div><label>Трек-код</label><input type="text" name="code" placeholder="TAJWAY2024XXX" required></div>
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
          <td><strong style="color:#6366f1">{{code}}</strong></td>
          <td><input type="text" name="client" value="{{info.client or ''}}" style="width:140px;"></td>
          <td><input type="number" name="weight" value="{{info.weight or 0}}" step="0.1" style="width:80px;"></td>
          <td>
            <select name="stage" style="width:130px;">
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

# ============ ОҒОЗ ============
if __name__ == '__main__':
    print('=' * 55)
    print('🚚  TAJWAY CARGO — Сервер фаъол шуд')
    print('=' * 55)
    print('🌐 Сайт:        http://localhost:5000')
    print('🔐 Админ:       http://localhost:5000/admin')
    print('   Логин:       admin')
    print('   Парол:       tajway2024')
    print('💰 Нарх:        27 сомонӣ / кг')
    print('=' * 55)
    app.run(host='0.0.0.0', port=5000, debug=True)
