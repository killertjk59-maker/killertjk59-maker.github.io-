from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, Response
import json
import os
import csv
import io
import uuid
import requests
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'akelcargo-secret-key-2026-change-me')

# ============ ТАНЗИМОТ ============
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'Komiljon')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Komiljon Orifjonzoda')

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
ADMIN_TELEGRAM_IDS = [x.strip() for x in os.environ.get('ADMIN_TELEGRAM_IDS', '8075805186').split(',') if x.strip()]
PUBLIC_URL = os.environ.get('PUBLIC_URL', '').rstrip('/')
TG_API = f'https://api.telegram.org/bot{BOT_TOKEN}' if BOT_TOKEN else None

TRACKS_FILE = 'tracks.json'
TICKETS_FILE = 'tickets.json'
CUSTOMERS_FILE = 'customers.json'
SETTINGS_FILE = 'settings.json'

STAGES = ['Дар анбори Хитой', 'Дар роҳ', 'Расид ба Тоҷикистон', 'Супорида шуд']

DEFAULT_SETTINGS = {
    'price_auto': 25,
    'price_avia': 60,
    'delivery_auto_days': '15-30 рӯз',
    'delivery_avia_days': '3-7 рӯз',
    'china_name': 'KHMIR',
    'china_phone': '15625450102',
    'china_address': '浙江省金华市义乌市 商城大道与柳青路交叉口东北220米洪华小区102栋2单元一楼',
    'china_note': '(MIR nom tel)',
    'tj_address': 'ш. Истаравшон, рӯ ба рӯи "Манзили Сафо"',
    'tj_phone': '+992 71 555 50 00',
    'telegram_handle': 'Akelcargo',
    'instagram_handle': 'Akelcargo',
}

# ============ ПОЙГОҲИ МАЪЛУМОТ (JSON) ============
def _load(path, default):
    if not os.path.exists(path):
        _save(path, default)
        return default
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return default

def _save(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_tracks():
    return _load(TRACKS_FILE, {
        'AKEL2026001': {'type': 'auto', 'client': 'Намуна 1', 'weight': 5.2, 'stage': 1, 'updated': '2026-06-20'},
        'AKEL2026002': {'type': 'avia', 'client': 'Намуна 2', 'weight': 2.5, 'stage': 2, 'updated': '2026-06-21'},
    })

def save_tracks(d): _save(TRACKS_FILE, d)

def load_tickets(): return _load(TICKETS_FILE, {})
def save_tickets(d): _save(TICKETS_FILE, d)

def load_customers(): return _load(CUSTOMERS_FILE, {})
def save_customers(d): _save(CUSTOMERS_FILE, d)

def load_settings():
    s = _load(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
    for k, v in DEFAULT_SETTINGS.items():
        s.setdefault(k, v)
    return s

def save_settings(d): _save(SETTINGS_FILE, d)

# ============ TELEGRAM API ============
def tg(method, **params):
    if not TG_API:
        return {}
    try:
        r = requests.post(f'{TG_API}/{method}', json=params, timeout=15)
        return r.json()
    except Exception:
        return {}

def notify_admins(text):
    for aid in ADMIN_TELEGRAM_IDS:
        tg('sendMessage', chat_id=aid, text=text, parse_mode='HTML')

def send_to_customer(telegram_id, text):
    if telegram_id:
        tg('sendMessage', chat_id=telegram_id, text=text, parse_mode='HTML')

def setup_webhook():
    if TG_API and PUBLIC_URL:
        tg('setWebhook', url=f'{PUBLIC_URL}/telegram/webhook')

setup_webhook()

# ============ ҲИМОЯИ АДМИН ============
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ============ САҲИФАИ АСОСӢ (HTML) ============
INDEX_HTML = r"""<!DOCTYPE html>
<html lang="tg">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Akelcargo — Карго аз Чин ба Тоҷикистон</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='31' fill='%23ffaa00'/%3E%3Cpath d='M32 12 L48 42 H40.5 L32 25 L23.5 42 H16 Z' fill='%231e3c72'/%3E%3Crect x='27' y='34' width='10' height='4.5' rx='1.2' fill='%23fff'/%3E%3C/svg%3E">
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', Tahoma, sans-serif; }
body { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); min-height:100vh; color:#fff; }
.container { max-width:1100px; margin:0 auto; padding:20px; }
a { text-decoration:none; color:inherit; }

header { text-align:center; padding:30px 20px 20px; }
.brand-logo { display:block; margin:0 auto 10px; filter:drop-shadow(0 6px 16px rgba(0,0,0,0.35)); }
header h1 { font-size:34px; font-weight:800; letter-spacing:1px; }
header h1 .logo-accent { color:#ffd700; }
header p { color:#cfd9ee; margin-top:6px; font-size:14px; }

nav { display:flex; justify-content:center; gap:6px; flex-wrap:wrap; background:rgba(0,0,0,0.2); border-radius:14px; padding:8px; margin:0 auto 20px; max-width:640px; }
nav a { padding:9px 14px; border-radius:10px; font-size:13px; font-weight:600; color:#dbe4f7; }
nav a:hover { background:rgba(255,255,255,0.12); }

.card { background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.12); border-radius:16px; padding:22px; margin-bottom:18px; backdrop-filter: blur(6px); }
.card h2 { margin-bottom:14px; font-size:19px; }

.price-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:18px; }
.price-card { border-radius:16px; padding:18px; text-align:center; }
.price-card.auto { background:linear-gradient(135deg,#ffd7d0,#ffb199); color:#5a1a0a; }
.price-card.avia { background:linear-gradient(135deg,#cfe4ff,#9fc4ff); color:#0a2a5a; }
.price-card .num { font-size:30px; font-weight:800; }
.price-card .lbl { font-size:12.5px; font-weight:700; margin-top:2px; }
.price-card .sub { font-size:11px; opacity:0.8; margin-top:4px; }

.feature-row { display:flex; justify-content:space-between; gap:8px; background:#fff; border-radius:16px; padding:16px 10px; margin-bottom:18px; flex-wrap:wrap; }
.feature-item { flex:1; min-width:70px; text-align:center; color:#1e3c72; }
.feature-item .fi { font-size:22px; }
.feature-item .ft { font-size:10.5px; font-weight:700; margin-top:4px; }

.market-row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:18px; }
.market-chip { flex:1; min-width:80px; text-align:center; padding:14px 8px; border-radius:12px; font-weight:800; font-size:13px; color:#fff; }
.m1{background:#e2231a;} .m2{background:#ff7a1a;} .m3{background:#ff5722;} .m4{background:#111;}

.calc-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px; }
.calc-grid label { display:block; font-size:12.5px; color:#dbe4f7; margin-bottom:5px; }
.calc-grid input, .calc-grid select, .track-form input, .ticket-form input, .ticket-form textarea {
  width:100%; padding:11px 12px; border-radius:10px; border:none; font-size:14.5px; color:#222;
}
.calc-result { background:rgba(255,255,255,0.15); border-radius:12px; padding:14px; text-align:center; }
.calc-result .price { font-size:26px; font-weight:800; color:#ffd700; }
.calc-result .detail { font-size:12.5px; color:#dbe4f7; margin-top:4px; }

.track-form { display:flex; gap:10px; margin-bottom:14px; }
.track-form input { flex:1; }
.btn { background:#ffd700; color:#1e3c72; border:none; padding:11px 20px; border-radius:10px; font-weight:800; cursor:pointer; font-size:14px; }
.btn:active { transform:scale(0.97); }
.result-box { background:rgba(255,255,255,0.12); border-radius:12px; padding:16px; margin-top:10px; }
.stage-track { display:flex; justify-content:space-between; margin-top:14px; }
.stage-dot { flex:1; text-align:center; font-size:11px; position:relative; color:#9fb3d9; }
.stage-dot.done { color:#ffd700; font-weight:700; }
.stage-dot .dot { width:12px; height:12px; border-radius:50%; background:#4a6cae; margin:0 auto 6px; }
.stage-dot.done .dot { background:#ffd700; }

.address-box { background:rgba(255,255,255,0.1); border-radius:12px; padding:16px; margin-bottom:12px; }
.address-box h3 { font-size:15px; margin-bottom:10px; }
.address-text { background:rgba(0,0,0,0.25); border-radius:10px; padding:12px; font-family:monospace; font-size:12.5px; line-height:1.7; white-space:pre-line; margin-bottom:10px; }
.copy-btn { background:#ffd700; color:#1e3c72; border:none; padding:9px 16px; border-radius:8px; font-weight:700; cursor:pointer; font-size:12.5px; }
.hint { font-size:12px; color:#cfd9ee; margin-top:10px; line-height:1.5; }

.ticket-form { display:flex; flex-direction:column; gap:10px; margin-bottom:16px; }
.ticket-form textarea { min-height:80px; resize:vertical; }
.tickets-list .t-item { background:rgba(255,255,255,0.08); border-radius:10px; padding:12px; margin-bottom:8px; font-size:13px; }
.tickets-list .t-answer { background:rgba(255,215,0,0.15); border-radius:8px; padding:8px 10px; margin-top:8px; color:#ffe9a8; font-size:12.5px; }

.profile-box { text-align:center; }
.profile-avatar { width:60px; height:60px; border-radius:50%; background:linear-gradient(135deg,#ffd700,#ffaa00); display:flex; align-items:center; justify-content:center; font-size:26px; margin:0 auto 10px; }
.profile-name { font-size:18px; font-weight:800; }
.profile-phone { font-size:13px; color:#cfd9ee; margin-top:2px; }

.contact-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.contact-card { background:rgba(255,255,255,0.1); border-radius:12px; padding:16px; text-align:center; }
.contact-card .icon { font-size:22px; }
.contact-card .label { font-size:11px; color:#cfd9ee; margin-top:4px; }
.contact-card .value { font-size:13px; font-weight:700; margin-top:2px; }

footer { text-align:center; padding:24px 10px; color:#9fb3d9; font-size:12px; }
</style>
</head>
<body>
<div class="container">
  <header>
    <svg class="brand-logo" width="76" height="76" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <defs><linearGradient id="logoBg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#ffd700"/><stop offset="100%" stop-color="#ffaa00"/>
      </linearGradient></defs>
      <circle cx="32" cy="32" r="31" fill="url(#logoBg)"/>
      <circle cx="32" cy="32" r="31" fill="none" stroke="#ffffff55" stroke-width="1.5"/>
      <path d="M10 40 A26 26 0 0 1 54 40" fill="none" stroke="#1e3c72aa" stroke-width="2" stroke-dasharray="1 5" stroke-linecap="round"/>
      <path d="M32 12 L48 42 H40.5 L32 25 L23.5 42 H16 Z" fill="#1e3c72"/>
      <rect x="27" y="34" width="10" height="4.5" rx="1.2" fill="#fff"/>
      <g transform="translate(15,44)">
        <rect x="0" y="0" width="20" height="7" rx="1.5" fill="#1e3c72"/>
        <path d="M20 1.5 H26 L30 6 V7 H20 Z" fill="#1e3c72"/>
        <circle cx="6" cy="8.3" r="2.4" fill="#1e3c72"/><circle cx="24" cy="8.3" r="2.4" fill="#1e3c72"/>
        <circle cx="6" cy="8.3" r="1" fill="#ffd700"/><circle cx="24" cy="8.3" r="1" fill="#ffd700"/>
      </g>
    </svg>
    <h1>Akel<span class="logo-accent">cargo</span></h1>
    <p>📦 Карго аз Чин ба Тоҷикистон • Зуд, бехатар, боэътимод</p>
  </header>

  <nav>
    <a href="#home">🏠 Асосӣ</a>
    <a href="#prices">💰 Нархҳо</a>
    <a href="#address">📍 Адресҳо</a>
    <a href="#track">🔍 Трек</a>
    <a href="#ticket-sec">✉️ Савол</a>
    <a href="#profile">👤 Профил</a>
  </nav>

  <!-- HOME -->
  <div id="home">
    <div class="price-grid">
      <div class="price-card auto">
        <div class="num">{{ s.price_auto }} сом</div>
        <div class="lbl">🚚 Авто / кг</div>
        <div class="sub">Мӯҳлат: {{ s.delivery_auto_days }}</div>
      </div>
      <div class="price-card avia">
        <div class="num">{{ s.price_avia }} сом</div>
        <div class="lbl">✈️ Авиа / кг</div>
        <div class="sub">Мӯҳлат: {{ s.delivery_avia_days }}</div>
      </div>
    </div>

    <div class="feature-row">
      <div class="feature-item"><div class="fi">🛡</div><div class="ft">Боэътимод</div></div>
      <div class="feature-item"><div class="fi">⚡</div><div class="ft">Тез</div></div>
      <div class="feature-item"><div class="fi">📦</div><div class="ft">Пайгирӣ</div></div>
      <div class="feature-item"><div class="fi">☎️</div><div class="ft">24/7</div></div>
      <div class="feature-item"><div class="fi">💵</div><div class="ft">Нархи хуб</div></div>
    </div>

    <div class="card">
      <h2>🛍 Фармоиш аз бозорҳои Хитой</h2>
      <p style="font-size:13px;color:#cfd9ee;margin-bottom:12px;">Аз ин платформаҳо фармоиш диҳед, адреси анбори моро (бахши "Адресҳо") нависед:</p>
      <div class="market-row">
        <div class="market-chip m1">Pinduoduo</div>
        <div class="market-chip m2">Taobao</div>
        <div class="market-chip m3">1688</div>
        <div class="market-chip m4">Poizon</div>
      </div>
    </div>
  </div>

  <!-- PRICES -->
  <div class="card" id="prices">
    <h2>💰 Калкулятори нарх</h2>
    <div class="calc-grid">
      <div>
        <label>Навъи интиқол</label>
        <select id="calcType" onchange="calculate()">
          <option value="auto">🚚 Авто — {{ s.price_auto }} сом/кг</option>
          <option value="avia">✈️ Авиа — {{ s.price_avia }} сом/кг</option>
        </select>
      </div>
      <div>
        <label>Вазн (кг)</label>
        <input type="number" id="calcWeight" placeholder="Масалан: 5.5" step="0.1" min="0" oninput="calculate()">
      </div>
    </div>
    <div class="calc-result">
      <div class="price" id="calcPrice">0 сомонӣ</div>
      <div class="detail" id="calcDetail">Вазн ва навъро интихоб кунед</div>
    </div>
  </div>

  <!-- TRACK -->
  <div class="card" id="track">
    <h2>🔍 Санҷиши трек-код</h2>
    <div class="track-form">
      <input type="text" id="trackInput" placeholder="Масалан: AKEL2026001" autocomplete="off">
      <button class="btn" onclick="searchTrack()">Ҷустуҷӯ</button>
    </div>
    <div id="trackResult"></div>
  </div>

  <!-- ADDRESS -->
  <div class="card" id="address">
    <h2>📍 Адреси анбор</h2>
    <div class="address-box">
      <h3>🇨🇳 Анбор дар Хитой</h3>
      <div class="address-text" id="addrChina">{{ s.china_name }} {{ s.china_phone }}
{{ s.china_address }}
{{ s.china_note }}</div>
      <button class="copy-btn" onclick="copyText('addrChina', this)">📋 Нусхабардорӣ</button>
      <p class="hint">⚠️ Ин адрес барои <strong>ҳамаи мизоҷон якхела</strong> аст — коди шахсӣ лозим нест. Ҳангоми фармоиш аз Taobao/1688/Pinduoduo/Poizon танҳо ҳамин адресро дар "адреси гиранда" нависед.</p>
    </div>
    <div class="address-box">
      <h3>🇹🇯 Анбор дар Тоҷикистон</h3>
      <div class="address-text" id="addrTj">{{ s.tj_address }}
Тел: {{ s.tj_phone }}</div>
      <button class="copy-btn" onclick="copyText('addrTj', this)">📋 Нусхабардорӣ</button>
    </div>
  </div>

  <!-- TICKETS -->
  <div class="card" id="ticket-sec">
    <h2>✉️ Маркази дастгирӣ ва саволҳо</h2>
    <p style="color:#cfd9ee;margin-bottom:14px;font-size:13px;">Саволи худро нависед — админ фавран ҷавоб медиҳад (ҳам дар сайт, ҳам дар Telegram)!</p>
    <form class="ticket-form" id="ticketForm" onsubmit="submitTicket(event)">
      <input type="text" id="ticketName" placeholder="Номи шумо" required>
      <input type="text" id="ticketContact" placeholder="Телефон ё Telegram барои тамос" required>
      <textarea id="ticketQuestion" placeholder="Саволи худро дар ин ҷо нависед..." required></textarea>
      <button type="submit" class="btn">✈️ Фиристодани савол</button>
    </form>
    <h3 style="margin:16px 0 10px;font-size:15px;">💬 Саволҳои охирин:</h3>
    <div id="ticketsList" class="tickets-list"></div>
  </div>

  <!-- PROFILE -->
  <div class="card" id="profile">
    <h2>👤 Профили ман</h2>
    <div class="profile-box">
      <div class="profile-avatar">👤</div>
      <div class="profile-name" id="profName">Меҳмон</div>
      <div class="profile-phone" id="profPhone">Барои сабт, боти Telegram-и моро кушоед ва /start фиристед</div>
    </div>
  </div>

  <!-- CONTACT -->
  <div class="card" id="contact">
    <h2>📞 Тамос бо мо</h2>
    <div class="contact-grid">
      <a href="https://t.me/{{ s.telegram_handle }}" class="contact-card" target="_blank">
        <div class="icon">✈️</div><div class="label">Telegram</div><div class="value">@{{ s.telegram_handle }}</div>
      </a>
      <a href="https://instagram.com/{{ s.instagram_handle }}" class="contact-card" target="_blank">
        <div class="icon">📷</div><div class="label">Instagram</div><div class="value">@{{ s.instagram_handle }}</div>
      </a>
      <a href="tel:{{ s.tj_phone }}" class="contact-card">
        <div class="icon">📞</div><div class="label">Телефон</div><div class="value">{{ s.tj_phone }}</div>
      </a>
      <a href="/admin" class="contact-card">
        <div class="icon">🔐</div><div class="label">Админ панел</div><div class="value">Воридшавӣ</div>
      </a>
    </div>
  </div>

  <footer>© 2026 Akelcargo. Ҳамаи ҳуқуқҳо ҳифз карда шудаанд.</footer>
</div>

<script>
const PRICE_AUTO = {{ s.price_auto }};
const PRICE_AVIA = {{ s.price_avia }};
const STAGES = {{ stages_json|safe }};
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) { tg.ready(); tg.expand(); }
const initData = tg ? tg.initData : "";
const tgUser = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) ? tg.initDataUnsafe.user : null;

function calculate() {
  const type = document.getElementById('calcType').value;
  const w = parseFloat(document.getElementById('calcWeight').value) || 0;
  const price = type === 'avia' ? PRICE_AVIA : PRICE_AUTO;
  const total = (w * price).toFixed(1);
  document.getElementById('calcPrice').textContent = total + ' сомонӣ';
  document.getElementById('calcDetail').textContent = w + ' кг × ' + price + ' сомонӣ (' + (type==='avia'?'Авиа':'Авто') + ')';
}

function copyText(id, btn) {
  const text = document.getElementById(id).textContent;
  navigator.clipboard.writeText(text).then(() => {
    const old = btn.textContent;
    btn.textContent = '✅ Нусхабардорӣ шуд';
    setTimeout(() => btn.textContent = old, 1800);
  });
}

function searchTrack() {
  const code = document.getElementById('trackInput').value.trim();
  const box = document.getElementById('trackResult');
  if (!code) return;
  box.innerHTML = '<p style="color:#cfd9ee;">Санҷида истодааст...</p>';
  fetch('/api/track/' + encodeURIComponent(code)).then(r => r.json()).then(d => {
    if (!d.found) { box.innerHTML = '<div class="result-box">❌ Трек-код ёфт нашуд.</div>'; return; }
    const t = d.track;
    let dots = '';
    STAGES.forEach((s, i) => {
      dots += '<div class="stage-dot ' + (i <= t.stage ? 'done' : '') + '"><div class="dot"></div>' + s + '</div>';
    });
    box.innerHTML = '<div class="result-box"><strong>' + code.toUpperCase() + '</strong> — ' +
      (t.type === 'avia' ? '✈️ Авиа' : '🚚 Авто') + ' • ' + (t.weight || '-') + ' кг<br>' +
      '<div class="stage-track">' + dots + '</div></div>';
  });
}

function submitTicket(e) {
  e.preventDefault();
  const body = {
    name: document.getElementById('ticketName').value,
    contact: document.getElementById('ticketContact').value,
    question: document.getElementById('ticketQuestion').value,
    telegram_id: tgUser ? tgUser.id : null,
  };
  fetch('/api/tickets', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
    .then(r => r.json()).then(() => {
      document.getElementById('ticketForm').reset();
      loadTickets();
      alert('Саволи шумо фиристода шуд ✅');
    });
}

function loadTickets() {
  fetch('/api/tickets').then(r => r.json()).then(list => {
    const box = document.getElementById('ticketsList');
    if (!list.length) { box.innerHTML = '<p style="color:#cfd9ee;font-size:13px;">Ҳанӯз савол нест.</p>'; return; }
    box.innerHTML = list.slice(0, 8).map(t =>
      '<div class="t-item"><strong>' + t.name + ':</strong> ' + t.question +
      (t.answer ? '<div class="t-answer">💬 Ҷавоб: ' + t.answer + '</div>' : '<div style="color:#cfd9ee;font-size:11.5px;margin-top:6px;">⏳ Интизори ҷавоб...</div>') +
      '</div>'
    ).join('');
  });
}

function loadProfile() {
  if (!tgUser) return;
  fetch('/api/profile?telegram_id=' + tgUser.id).then(r => r.json()).then(d => {
    if (d.registered) {
      document.getElementById('profName').textContent = d.user.name || tgUser.first_name;
      document.getElementById('profPhone').textContent = d.user.phone || '';
    } else {
      document.getElementById('profName').textContent = tgUser.first_name || 'Мизоҷ';
      document.getElementById('profPhone').textContent = 'Барои сабти телефон, /start-ро дар бот такрор фиристед';
    }
  });
}

loadTickets();
loadProfile();
</script>
</body>
</html>
"""

# ============ АДМИН: LOGIN ============
LOGIN_HTML = r"""<!DOCTYPE html>
<html lang="tg"><head><meta charset="UTF-8"><title>Воридшавӣ — Akelcargo Admin</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', Tahoma, sans-serif; }
body { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); min-height:100vh; display:flex; align-items:center; justify-content:center; color:#fff; }
.box { background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15); border-radius:18px; padding:32px; width:90%; max-width:360px; text-align:center; }
h1 { font-size:20px; margin-bottom:20px; }
input { width:100%; padding:12px; border-radius:10px; border:none; margin-bottom:12px; font-size:14.5px; }
button { width:100%; padding:12px; border-radius:10px; border:none; background:#ffd700; color:#1e3c72; font-weight:800; cursor:pointer; }
.err { color:#ff8080; font-size:13px; margin-bottom:10px; }
</style></head>
<body>
<form class="box" method="POST">
  <h1>🔐 Akelcargo Admin</h1>
  {% if error %}<div class="err">{{ error }}</div>{% endif %}
  <input type="text" name="username" placeholder="Логин" required>
  <input type="password" name="password" placeholder="Парол" required>
  <button type="submit">Воридшавӣ</button>
</form>
</body></html>
"""

# ============ АДМИН: ПАНЕЛ ============
PANEL_HTML = r"""<!DOCTYPE html>
<html lang="tg"><head><meta charset="UTF-8"><title>Панели идоракунӣ — Akelcargo</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', Tahoma, sans-serif; }
body { background:#0f1117; color:#eee; min-height:100vh; }
.wrap { max-width:1000px; margin:0 auto; padding:18px; }
h1 { font-size:20px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;}
a.pill, button.pill { background:#1e3c72; color:#fff; border:none; padding:8px 14px; border-radius:20px; font-size:12.5px; text-decoration:none; cursor:pointer; }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:10px; margin-bottom:20px; }
.stat { background:#181b26; border-radius:14px; padding:16px; border-top:3px solid #ffd700; }
.stat .n { font-size:24px; font-weight:800; }
.stat .l { font-size:11.5px; color:#9aa4c0; margin-top:2px; }
.section { background:#181b26; border-radius:14px; padding:18px; margin-bottom:18px; }
.section h2 { font-size:15px; margin-bottom:12px; color:#ffd700; }
table { width:100%; border-collapse:collapse; font-size:12.5px; }
th, td { text-align:left; padding:8px 6px; border-bottom:1px solid #2a2e3d; }
th { color:#9aa4c0; font-weight:600; }
input, select, textarea { background:#0f1117; border:1px solid #2a2e3d; color:#eee; padding:8px 10px; border-radius:8px; font-size:13px; }
.row { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px; }
.row > * { flex:1; min-width:110px; }
button.act { background:#ffd700; color:#1e3c72; border:none; padding:8px 14px; border-radius:8px; font-weight:700; cursor:pointer; font-size:12.5px; }
button.del { background:#a33; color:#fff; border:none; padding:6px 10px; border-radius:6px; cursor:pointer; font-size:11.5px; }
button.ans { background:#2a7; color:#fff; border:none; padding:6px 10px; border-radius:6px; cursor:pointer; font-size:11.5px; }
.badge { padding:2px 8px; border-radius:20px; font-size:10.5px; font-weight:700; }
.badge.open { background:#a33; } .badge.answered { background:#2a7; }
</style></head>
<body>
<div class="wrap">
  <h1>🔐 Akelcargo — Панели идоракунӣ
    <span>
      <a class="pill" href="/" target="_blank">🌐 Сайт</a>
      <a class="pill" href="/admin/export.csv">⬇️ Экспорт CSV</a>
      <a class="pill" href="/admin/logout">Баромад</a>
    </span>
  </h1>

  <div class="stats">
    <div class="stat"><div class="n">{{ stats.customers }}</div><div class="l">Мизоҷон</div></div>
    <div class="stat"><div class="n">{{ stats.auto }}</div><div class="l">Трекҳои Авто</div></div>
    <div class="stat"><div class="n">{{ stats.avia }}</div><div class="l">Трекҳои Авиа</div></div>
    <div class="stat"><div class="n">{{ stats.arrived }}</div><div class="l">Расидаҳо</div></div>
    <div class="stat"><div class="n">{{ stats.open_tickets }}</div><div class="l">Тикети кушода</div></div>
    <div class="stat"><div class="n">{{ stats.total_tickets }}</div><div class="l">Ҳамаи тикетҳо</div></div>
  </div>

  <div class="section">
    <h2>💰 Нархҳо ва танзимот</h2>
    <form method="POST" action="/admin/settings" class="row">
      <input name="price_auto" type="number" step="0.1" value="{{ s.price_auto }}" placeholder="Нархи Авто">
      <input name="price_avia" type="number" step="0.1" value="{{ s.price_avia }}" placeholder="Нархи Авиа">
      <input name="tj_address" value="{{ s.tj_address }}" placeholder="Адреси Истаравшон" style="flex:2;">
      <input name="tj_phone" value="{{ s.tj_phone }}" placeholder="Телефон">
      <button class="act" type="submit">💾 Захира</button>
    </form>
  </div>

  <div class="section">
    <h2>📦 Илова кардани трек</h2>
    <form method="POST" action="/admin/tracks/add" class="row">
      <input name="code" placeholder="Трек-код (AKEL2026003)" required>
      <select name="type"><option value="auto">🚚 Авто</option><option value="avia">✈️ Авиа</option></select>
      <input name="client" placeholder="Ном/телефони мизоҷ">
      <input name="weight" type="number" step="0.1" placeholder="Вазн (кг)">
      <select name="stage">
        {% for st in stages %}<option value="{{ loop.index0 }}">{{ st }}</option>{% endfor %}
      </select>
      <button class="act" type="submit">➕ Илова</button>
    </form>
    <table>
      <tr><th>Код</th><th>Навъ</th><th>Мизоҷ</th><th>Вазн</th><th>Ҳолат</th><th></th></tr>
      {% for code, t in tracks.items() %}
      <tr>
        <td>{{ code }}</td>
        <td>{{ '✈️' if t.type=='avia' else '🚚' }}</td>
        <td>{{ t.client or '-' }}</td>
        <td>{{ t.weight or '-' }}</td>
        <td>{{ stages[t.stage] }}</td>
        <td><a class="pill" href="/admin/tracks/delete/{{ code }}" onclick="return confirm('Тоза кардан?')">🗑</a></td>
      </tr>
      {% endfor %}
    </table>
  </div>

  <div class="section">
    <h2>✉️ Тикетҳо</h2>
    {% for tid, t in tickets.items() %}
    <div style="border-bottom:1px solid #2a2e3d;padding:10px 0;">
      <div><strong>{{ t.name }}</strong> ({{ t.contact }}) — <span class="badge {{ 'answered' if t.answer else 'open' }}">{{ 'Ҷавоб дода шуд' if t.answer else 'Кушода' }}</span></div>
      <div style="color:#9aa4c0;font-size:12.5px;margin:4px 0;">{{ t.question }}</div>
      {% if t.answer %}<div style="color:#8fd; font-size:12px;">💬 {{ t.answer }}</div>{% endif %}
      {% if not t.answer %}
      <form method="POST" action="/admin/tickets/answer/{{ tid }}" class="row" style="margin-top:6px;">
        <input name="answer" placeholder="Ҷавоби худро нависед..." required style="flex:3;">
        <button class="ans" type="submit">✅ Ҷавоб додан</button>
      </form>
      {% endif %}
    </div>
    {% endfor %}
  </div>

  <div class="section">
    <h2>👥 Мизоҷон ({{ stats.customers }})</h2>
    <table>
      <tr><th>Ном</th><th>Телефон</th><th>Telegram ID</th><th>Сана</th></tr>
      {% for tid, c in customers.items() %}
      <tr><td>{{ c.name }}</td><td>{{ c.phone or '-' }}</td><td>{{ tid }}</td><td>{{ c.created_at[:10] }}</td></tr>
      {% endfor %}
    </table>
  </div>

  <div class="section">
    <h2>📢 Хабар ба ҳамаи мизоҷон</h2>
    <form method="POST" action="/admin/broadcast" class="row">
      <textarea name="text" placeholder="Матни хабар..." style="flex:3;min-height:60px;" required></textarea>
      <button class="act" type="submit">📢 Фиристодан</button>
    </form>
  </div>
</div>
</body></html>
"""

# ============ ROUTES: ПУБЛИКӢ ============
@app.route('/')
def index():
    s = load_settings()
    return render_template_string(INDEX_HTML, s=s, stages_json=json.dumps(STAGES, ensure_ascii=False))

@app.route('/api/track/<code>')
def api_track(code):
    tracks = load_tracks()
    t = tracks.get(code.strip().upper())
    if not t:
        return jsonify({'found': False})
    return jsonify({'found': True, 'track': t})

@app.route('/api/profile')
def api_profile():
    telegram_id = request.args.get('telegram_id')
    customers = load_customers()
    c = customers.get(str(telegram_id))
    if not c:
        return jsonify({'registered': False})
    return jsonify({'registered': True, 'user': c})

@app.route('/api/tickets', methods=['GET', 'POST'])
def api_tickets():
    tickets = load_tickets()
    if request.method == 'POST':
        data = request.get_json(force=True, silent=True) or {}
        tid = str(uuid.uuid4())[:8]
        tickets[tid] = {
            'name': data.get('name', '').strip() or 'Меҳмон',
            'contact': data.get('contact', '').strip(),
            'question': data.get('question', '').strip(),
            'telegram_id': data.get('telegram_id'),
            'answer': None,
            'created_at': datetime.utcnow().isoformat(),
        }
        save_tickets(tickets)
        notify_admins(f"✉️ <b>Саволи нав аз сайт</b>\n{tickets[tid]['name']} ({tickets[tid]['contact']})\n{tickets[tid]['question']}\n\nҶавоб дар: {PUBLIC_URL}/admin")
        return jsonify({'ok': True, 'id': tid})
    # GET — рӯйхати охирин (аз нав ба кӯҳна)
    items = [dict(id=k, **v) for k, v in tickets.items()]
    items.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify(items)


# ============ ROUTES: АДМИН ============
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin'):
        return redirect(url_for('admin_panel'))
    error = None
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USERNAME and request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        error = 'Логин ё парол нодуруст аст'
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/panel')
@login_required
def admin_panel():
    tracks = load_tracks()
    tickets = load_tickets()
    customers = load_customers()
    s = load_settings()
    stats = {
        'customers': len(customers),
        'auto': sum(1 for t in tracks.values() if t.get('type') == 'auto'),
        'avia': sum(1 for t in tracks.values() if t.get('type') == 'avia'),
        'arrived': sum(1 for t in tracks.values() if t.get('stage', 0) >= 2),
        'open_tickets': sum(1 for t in tickets.values() if not t.get('answer')),
        'total_tickets': len(tickets),
    }
    tickets_sorted = dict(sorted(tickets.items(), key=lambda kv: kv[1]['created_at'], reverse=True))
    return render_template_string(PANEL_HTML, stats=stats, tracks=tracks, tickets=tickets_sorted,
                                   customers=customers, s=s, stages=STAGES)

@app.route('/admin/settings', methods=['POST'])
@login_required
def admin_settings():
    s = load_settings()
    s['price_auto'] = float(request.form.get('price_auto', s['price_auto']))
    s['price_avia'] = float(request.form.get('price_avia', s['price_avia']))
    s['tj_address'] = request.form.get('tj_address', s['tj_address'])
    s['tj_phone'] = request.form.get('tj_phone', s['tj_phone'])
    save_settings(s)
    return redirect(url_for('admin_panel'))

@app.route('/admin/tracks/add', methods=['POST'])
@login_required
def admin_tracks_add():
    tracks = load_tracks()
    code = request.form.get('code', '').strip().upper()
    if code:
        tracks[code] = {
            'type': request.form.get('type', 'auto'),
            'client': request.form.get('client', ''),
            'weight': float(request.form.get('weight') or 0),
            'stage': int(request.form.get('stage', 0)),
            'updated': datetime.utcnow().strftime('%Y-%m-%d'),
        }
        save_tracks(tracks)
    return redirect(url_for('admin_panel'))

@app.route('/admin/tracks/delete/<code>')
@login_required
def admin_tracks_delete(code):
    tracks = load_tracks()
    tracks.pop(code.strip().upper(), None)
    save_tracks(tracks)
    return redirect(url_for('admin_panel'))

@app.route('/admin/tickets/answer/<tid>', methods=['POST'])
@login_required
def admin_tickets_answer(tid):
    tickets = load_tickets()
    if tid in tickets:
        answer = request.form.get('answer', '').strip()
        tickets[tid]['answer'] = answer
        tickets[tid]['answered_at'] = datetime.utcnow().isoformat()
        save_tickets(tickets)
        tg_id = tickets[tid].get('telegram_id')
        if tg_id:
            send_to_customer(tg_id, f"💬 <b>Ҷавоб ба саволи шумо:</b>\n{tickets[tid]['question']}\n\n➡️ {answer}")
    return redirect(url_for('admin_panel'))

@app.route('/admin/broadcast', methods=['POST'])
@login_required
def admin_broadcast():
    text = request.form.get('text', '').strip()
    if text:
        customers = load_customers()
        for tid in customers.keys():
            send_to_customer(tid, f"📢 {text}")
    return redirect(url_for('admin_panel'))

@app.route('/admin/export.csv')
@login_required
def admin_export_csv():
    tracks = load_tracks()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['Код', 'Навъ', 'Мизоҷ', 'Вазн', 'Ҳолат', 'Сана'])
    for code, t in tracks.items():
        writer.writerow([code, t.get('type'), t.get('client'), t.get('weight'), STAGES[t.get('stage', 0)], t.get('updated')])
    return Response(out.getvalue(), mimetype='text/csv',
                     headers={'Content-Disposition': 'attachment;filename=akelcargo_tracks.csv'})

# ============ TELEGRAM WEBHOOK ============
MENU_KEYBOARD = {
    'keyboard': [
        [{'text': '📦 Санҷиши трек'}, {'text': '💰 Нархҳо'}],
        [{'text': '📍 Адрес'}, {'text': '✉️ Савол ба админ'}],
    ],
    'resize_keyboard': True,
}

def contact_keyboard():
    return {
        'keyboard': [[{'text': '📱 Фиристодани рақами телефон', 'request_contact': True}]],
        'resize_keyboard': True, 'one_time_keyboard': True,
    }

@app.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    update = request.get_json(force=True, silent=True) or {}
    msg = update.get('message')
    if not msg:
        return jsonify({'ok': True})

    chat_id = msg['chat']['id']
    from_user = msg.get('from', {})
    tgid = str(from_user.get('id'))
    text = (msg.get('text') or '').strip()
    s = load_settings()
    customers = load_customers()

    if 'contact' in msg:
        c = msg['contact']
        if str(c.get('user_id')) == tgid:
            customers[tgid] = {
                'name': from_user.get('first_name', ''),
                'username': from_user.get('username', ''),
                'phone': c.get('phone_number', ''),
                'created_at': datetime.utcnow().isoformat(),
            }
            save_customers(customers)
            tg('sendMessage', chat_id=chat_id, text='Ташаккур! Шумо сабт шудед ✅\n\nАз тугмаҳои поён истифода баред:',
               reply_markup=MENU_KEYBOARD)
            notify_admins(f"🆕 Мизоҷи нав: {customers[tgid]['name']} — {customers[tgid]['phone']}")
        return jsonify({'ok': True})

    if text == '/start':
        if tgid in customers:
            tg('sendMessage', chat_id=chat_id, text=f"Хуш омадед боз, {from_user.get('first_name','')} 👋",
               reply_markup=MENU_KEYBOARD)
        else:
            tg('sendMessage', chat_id=chat_id,
               text='Ба <b>Akelcargo</b> хуш омадед! 🚚📦\n\nБарои сабти шумо, лутфан рақами телефонро тавассути тугмаи поён фиристед.',
               parse_mode='HTML', reply_markup=contact_keyboard())
        return jsonify({'ok': True})

    if text == '💰 Нархҳо':
        tg('sendMessage', chat_id=chat_id,
           text=f"💰 <b>Нархҳо</b>\n🚚 Авто: {s['price_auto']} сом/кг ({s['delivery_auto_days']})\n✈️ Авиа: {s['price_avia']} сом/кг ({s['delivery_avia_days']})",
           parse_mode='HTML')
        return jsonify({'ok': True})

    if text == '📍 Адрес':
        tg('sendMessage', chat_id=chat_id,
           text=f"🇨🇳 <b>Хитой:</b>\n{s['china_name']} {s['china_phone']}\n{s['china_address']}\n{s['china_note']}\n\n🇹🇯 <b>Тоҷикистон:</b>\n{s['tj_address']}\nТел: {s['tj_phone']}",
           parse_mode='HTML')
        return jsonify({'ok': True})

    if text == '📦 Санҷиши трек':
        tg('sendMessage', chat_id=chat_id, text='Трек-кодро фиристед (масалан AKEL2026001):')
        return jsonify({'ok': True})

    if text == '✉️ Савол ба админ':
        tg('sendMessage', chat_id=chat_id, text='Саволи худро дар паёми навбатӣ нависед:')
        return jsonify({'ok': True})

    if text.startswith('/admin') and tgid in ADMIN_TELEGRAM_IDS:
        tg('sendMessage', chat_id=chat_id, text=f"🔐 Панели админ: {PUBLIC_URL}/admin")
        return jsonify({'ok': True})

    # Санҷиши мутобиқат ба трек-код
    tracks = load_tracks()
    tcode = text.strip().upper()
    if tcode in tracks:
        t = tracks[tcode]
        tg('sendMessage', chat_id=chat_id,
           text=f"📦 <b>{tcode}</b>\n{'✈️ Авиа' if t['type']=='avia' else '🚚 Авто'} • {t.get('weight','-')} кг\nҲолат: {STAGES[t.get('stage',0)]}",
           parse_mode='HTML')
        return jsonify({'ok': True})

    # Дигар — тикет
    if text:
        tickets = load_tickets()
        tid = str(uuid.uuid4())[:8]
        name = customers.get(tgid, {}).get('name') or from_user.get('first_name', 'Мизоҷ')
        contact = customers.get(tgid, {}).get('phone') or f"@{from_user.get('username','')}"
        tickets[tid] = {
            'name': name, 'contact': contact, 'question': text,
            'telegram_id': tgid, 'answer': None, 'created_at': datetime.utcnow().isoformat(),
        }
        save_tickets(tickets)
        tg('sendMessage', chat_id=chat_id, text='✅ Саволи шумо ба админ фиристода шуд, интизори ҷавоб бошед.')
        notify_admins(f"✉️ <b>Саволи нав аз Telegram</b>\n{name} ({contact})\n{text}\n\nҶавоб дар: {PUBLIC_URL}/admin")
    return jsonify({'ok': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
