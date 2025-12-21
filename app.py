import os
import json
import datetime
from flask import Flask, render_template_string, abort
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "cache.json"
HISTORY_FILE = "history.json"

AFFILIATE_TAG = "whoaccepts-21"

# --- PRODUCTS ---
PRODUCTS = [
    {
        "name": "VonShef 3 Tray Buffet Server & Hot Plate Food Warmer",
        "category": "Home & Kitchen",
        "image": "https://m.media-amazon.com/images/I/71kTQECp3FL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/VonShef-Tray-Warmer-Buffet-Server/dp/B073Q5G9VX?tag={AFFILIATE_TAG}",
        "info": "3-tray electric buffet server with adjustable temperature — keeps food warm for parties, hosting, or family meals. Top trending choice for holiday entertaining with easy clean trays."
    },
    {
        "name": "Driving Theory Test Kit UK 2025 with Highway Code Book",
        "category": "Books",
        "image": "https://m.media-amazon.com/images/I/81akIVih9NL._SY385_.jpg",
        "url": f"https://www.amazon.co.uk/UK-Driving-Theory-Test-Kit/dp/B09D84M7C4?tag={AFFILIATE_TAG}",
        "info": "Complete 2025 theory test kit with official Highway Code book, practice questions, hazard perception — essential for passing the UK driving test. Massive demand spike for new learners."
    },
    {
        "name": "Magnetic Chess Game with Stones Portable Family Board",
        "category": "Toys & Games",
        "image": "https://m.media-amazon.com/images/I/61mcbNi2MGL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Magnetic-Training-Chesss-Birthdays-Gatherings/dp/B0FMXLG87Y?tag={AFFILIATE_TAG}",
        "info": "Portable magnetic chess set with stones and ropes — fun family game for parties, travel, or gatherings. Addictive strategy challenge that's trending for all ages."
    },
    # add more products as needed...
]

# --- 6 Daily Rotating Themes ---
THEMES = [
    {"bg": "#0d0d1f", "card": "#161630", "accent": "#ff4e4e", "button": "#ff4e4e", "tag": "#8b5cf6", "text_accent": "#ff6b6b", "gradient": "linear-gradient(90deg,#ff4e4e,#8b5cf6)"},
    {"bg": "#0f172a", "card": "#1e293b", "accent": "#60a5fa", "button": "#3b82f6", "tag": "#93c5fd", "text_accent": "#93c5fd", "gradient": "linear-gradient(90deg,#3b82f6,#60a5fa)"},
    {"bg": "#111827", "card": "#1f2937", "accent": "#ef4444", "button": "#dc2626", "tag": "#22c55e", "text_accent": "#22c55e", "gradient": "linear-gradient(90deg,#dc2626,#22c55e)"},
    {"bg": "#0f172a", "card": "#164e63", "accent": "#06b6d4", "button": "#0891b2", "tag": "#22d3ee", "text_accent": "#67e8f9", "gradient": "linear-gradient(90deg,#0891b2,#22d3ee)"},
    {"bg": "#1e1b4b", "card": "#312e81", "accent": "#f97316", "button": "#ea580c", "tag": "#fb923c", "text_accent": "#fdba74", "gradient": "linear-gradient(90deg,#ea580c,#f97316)"},
    {"bg": "#022c22", "card": "#065f46", "accent": "#10b981", "button": "#059669", "tag": "#34d399", "text_accent": "#6ee7b7", "gradient": "linear-gradient(90deg,#059669,#34d399)"},
]

def get_daily_theme():
    day_of_year = datetime.date.today().timetuple().tm_yday
    theme_index = day_of_year % len(THEMES)
    return THEMES[theme_index]

# --- CSS Template ---
CSS_TEMPLATE = """ 
<style>
body{margin:0;background:{{bg}};color:#fff;font-family:'Outfit',sans-serif;padding:20px}
h1{text-align:center;font-size:3.5rem;background:{{gradient}};-webkit-background-clip:text;color:transparent}
.subtitle{text-align:center;opacity:.8;margin-bottom:40px;font-size:1.2rem;max-width:900px;margin-left:auto;margin-right:auto;color:{{text_accent}}}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;max-width:1400px;margin:auto}
.card{background:{{card}};border-radius:22px;padding:18px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.6);transition:.3s}
.card:hover{transform:scale(1.03)}
@media (max-width:768px){.grid{grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px;}.card{padding:20px;}}
img{width:100%;border-radius:16px;transition:0.3s;margin-top:10px;}
.card a img:hover{opacity:0.9;transform:scale(1.03)}
.tag{background:{{tag}};padding:6px 14px;border-radius:20px;font-size:.85rem;display:inline-block;margin-bottom:10px}
button{background:{{button}};border:none;padding:14px 36px;border-radius:50px;font-size:1.2rem;font-weight:900;color:white;cursor:pointer}
.hook{margin:14px 0;line-height:1.5;font-size:1.05rem}
footer{text-align:center;opacity:.6;margin:60px 0}
details {margin-top:16px;}
details summary {font-weight:900;font-size:1.1rem;color:{{accent}};cursor:pointer;display:inline-block;padding:10px 20px;background:{{card}};border:2px solid {{accent}};border-radius:50px;transition:0.3s;}
details summary:hover {background:{{accent}};color:white;}
details[open] summary {border-radius:50px 50px 0 0;}
details p {background:{{card}};padding:16px;border-radius:0 0 16px 16px;border:2px solid {{accent}};border-top:none;margin:0;font-size:0.9rem;opacity:0.9;}
.archive {margin-top:80px;}
.archive h2 {text-align:center;color:{{accent}};font-size:2.2rem;margin-bottom:40px;}
.archive details {margin-bottom:20px;}
.archive summary {font-size:1.5rem;cursor:pointer;color:{{text_accent}};}
.archive .category-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;margin-top:20px;}
.category-link {color:{{text_accent}};text-decoration:underline;cursor:pointer;margin:10px;display:inline-block;}
</style>
"""

# --- MAIN_HTML Template ---
MAIN_HTML = """ 
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FyboBuybo - Trending UK Deals</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">
{{ css | safe }}
</head>
<body>
<h1>FyboBuybo</h1>
<p class="subtitle">Discover the hottest UK deals right now — from seasonal gifts and essentials to viral gadgets everyone's buying. Updated daily with what's trending!</p>

<h2 style="text-align:center;font-size:2.4rem;margin:60px 0 40px;color:{{accent}};">Today's Trending Deals</h2>
<div class="grid">
{% for p in today_products %}
<div class="card">
  <span class="tag">{{ p.category }}</span>
  <h3>{{ p.name }}</h3>
  <a href="{{ p.url }}" target="_blank">
    <img src="{{ p.image }}" alt="{{ p.name }}">
  </a>
  <div class="hook">{{ p.hook|safe }}</div>
  <details>
    <summary>Read More ↓</summary>
    <p>{{ p.info }}</p>
  </details>
  <a href="{{ p.url }}" target="_blank">
    <button>Check Price</button>
  </a>
</div>
{% endfor %}
</div>

<div class="archive">
  <h2>Trend Archive – Explore Past Hot Deals</h2>
  <p style="text-align:center;">
  Browse by category: 
  {% for cat in categories %}
    {% set slug = cat|lower|replace(' & ', '-and-')|replace(' ', '-') %}
    <a href="/category/{{ slug }}" class="category-link">{{ cat }}</a>{% if not loop.last %} | {% endif %}
  {% endfor %}
</p>
  {% if archive_dates %}
    {% for date in archive_dates %}
    <details>
      <summary>{{ date }} ({{ archive[date]|length }} deals)</summary>
      {% set grouped = namespace(data={}) %}
      {% for p in archive[date] %}
        {% if grouped.data[p.category] is not defined %}
          {% set _ = grouped.data.update({p.category: []}) %}
        {% endif %}
        {% set _ = grouped.data[p.category].append(p) %}
      {% endfor %}
      {% for cat, items in grouped.data.items() %}
        <h3 style="text-align:left;color:{{text_accent}};margin:30px 0 10px;">{{ cat }}</h3>
        <div class="category-grid">
          {% for p in items %}
          <div class="card">
            <span class="tag">{{ p.category }}</span>
            <h3>{{ p.name }}</h3>
            <a href="{{ p.url }}" target="_blank">
              <img src="{{ p.image }}" alt="{{ p.name }}">
            </a>
            <div class="hook">{{ p.hook|safe }}</div>
            <a href="{{ p.url }}" target="_blank">
              <button>Check Price</button>
            </a>
          </div>
          {% endfor %}
        </div>
      {% endfor %}
    </details>
    {% endfor %}
  {% else %}
    <p style="text-align:center;">Archive building — check back tomorrow!</p>
  {% endif %}
</div>

<footer>Affiliate links may earn commission · Made with AI</footer>
</body>
</html>
"""

# --- CATEGORY_HTML Template ---
CATEGORY_HTML = """ 
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FyboBuybo - Archive: {{ category_title }}</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">
{{ css | safe }}
</head>
<body>
<h1>FyboBuybo</h1>
<p class="subtitle">Archive: All {{ category_title }} Deals</p>
<a href="/">← Back to Home</a>

<div class="grid">
{% for p in category_products %}
<div class="card">
  <span class="tag">{{ p.category }}</span>
  <h3>{{ p.name }}</h3>
  <a href="{{ p.url }}" target="_blank">
    <img src="{{ p.image }}" alt="{{ p.name }}">
  </a>
  <div class="hook">{{ p.hook|safe }}</div>
  <details>
    <summary>Read More ↓</summary>
    <p>{{ p.info }}</p>
  </details>
  <a href="{{ p.url }}" target="_blank">
    <button>Check Price</button>
  </a>
</div>
{% endfor %}
</div>

<footer>Affiliate links may earn commission · Made with AI</footer>
</body>
</html>
"""

# --- Helper Functions ---
def generate_hook(name):
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"Write a calm, elegant 1-2 sentence description highlighting the appeal of this trending UK Amazon product: '{name}'. Use <b> tags for subtle emphasis on key benefits. Keep it sophisticated and natural, with no forced urgency or shopping language."
            }],
            temperature=0.8,
            max_tokens=100
        )
        hook = r.choices[0].message.content.strip()
        return hook
    except Exception:
        return "Discover why this product is trending in the UK."

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_today_products():
    cache = load_cache()
    today_str = datetime.date.today().isoformat()
    today_products = []

    for p in PRODUCTS:
        key = f"{today_str}_{p['name']}"
        if key in cache:
            hook = cache[key]
        else:
            hook = generate_hook(p['name'])
            cache[key] = hook
        p_copy = p.copy()
        p_copy['hook'] = hook
        today_products.append(p_copy)

    save_cache(cache)
    return today_products

def build_archive(today_products):
    history = load_history()
    today_str = datetime.date.today().isoformat()
    history[today_str] = today_products
    save_history(history)
    return history

def get_categories():
    cats = set(p['category'] for p in PRODUCTS)
    return sorted(cats)

# --- Routes ---
@app.route("/")
def home():
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    today_products = get_today_products()
    archive = load_history()
    archive_dates = sorted(archive.keys(), reverse=True)
    categories = get_categories()
    return render_template_string(MAIN_HTML,
                                  css=css,
                                  today_products=today_products,
                                  archive=archive,
                                  archive_dates=archive_dates,
                                  categories=categories,
                                  **theme)

@app.route("/category/<slug>")
def category_page(slug):
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    cat_name = None
    for c in get_categories():
        s = c.lower().replace(" & ", "-and-").replace(" ", "-")
        if s == slug:
            cat_name = c
            break
    if not cat_name:
        abort(404)
    archive = load_history()
    category_products = []
    for products in archive.values():
        for p in products:
            if p['category'] == cat_name:
                category_products.append(p)
    return render_template_string(CATEGORY_HTML,
                                  css=css,
                                  category_title=cat_name,
                                  category_products=category_products,
                                  **theme)

if __name__ == "__main__":
    today_products = get_today_products()
    build_archive(today_products)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
