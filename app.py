import os
import json
import datetime
import re
from flask import Flask, render_template_string, abort, jsonify
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "cache.json"
HISTORY_FILE = "history.json"

AFFILIATE_TAG = "whoaccepts-21"

PRODUCTS = [
    # Same product data as before
    # ...
]

THEMES = [
    # Same theme data as before
    # ...
]

def get_daily_theme():
    day_of_year = datetime.date.today().timetuple().tm_yday
    theme_index = day_of_year % len(THEMES)
    return THEMES[theme_index]

CSS_TEMPLATE = """
<style>
body{margin:0;background:{{bg}};color:#fff;font-family:'Outfit',sans-serif;padding:20px}
h1{text-align:center;font-size:3.5rem;background:{{gradient}};-webkit-background-clip:text;color:transparent}
.subtitle{text-align:center;opacity:.8;margin-bottom:40px;font-size:1.2rem;max-width:900px;margin-left:auto;margin-right:auto;color:{{text_accent}}}

/* Tighter grid for desktop */
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;max-width:1400px;margin:auto}

/* Smaller cards on large screens */
.card{background:{{card}};border-radius:22px;padding:18px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.6);transition:.3s}
.card:hover{transform:scale(1.03)}

/* Mobile override */
@media (max-width:768px) {
  .grid{grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px;}
  .card{padding:20px;}
}

img{width:100%;border-radius:16px;transition:0.3s;margin-top:10px;}
.card a img:hover{opacity:0.9;transform:scale(1.03)}
.tag{background:{{tag}};padding:6px 14px;border-radius:20px;font-size:.85rem;display:inline-block;margin-bottom:10px}
button{background:{{button}};border:none;padding:14px 36px;border-radius:50px;font-size:1.2rem;font-weight:900;color:white;cursor:pointer}
.hook{margin:14px 0;line-height:1.5;font-size:1.05rem}
footer{text-align:center;opacity:.6;margin:60px 0}

/* "Read More" */
details {margin-top:16px;}
details summary {font-weight:900;font-size:1.1rem;color:{{accent}};cursor:pointer;display:inline-block;padding:10px 20px;background:{{card}};border:2px solid {{accent}};border-radius:50px;transition:0.3s;}
details summary:hover {background:{{accent}};color:white;}
details[open] summary {border-radius:50px 50px 0 0;}
details p {background:{{card}};padding:16px;border-radius:0 0 16px 16px;border:2px solid {{accent}};border-top:none;margin:0;font-size:0.9rem;opacity:0.9;}

/* Archive */
.archive {margin-top:80px;}
.archive h2 {text-align:center;color:{{accent}};font-size:2.2rem;margin-bottom:40px;}
.archive details {margin-bottom:20px;}
.archive summary {font-size:1.5rem;cursor:pointer;color:{{text_accent}};}
.archive .category-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;margin-top:20px;}
.category-link {color:{{text_accent}};text-decoration:underline;cursor:pointer;margin:10px;display:inline-block;}
</style>
"""

MAIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FyboBuybo - Trending UK Deals</title>
<meta name="description" content="Discover the best UK deals, from seasonal gifts to trending gadgets. Updated daily with the hottest products everyone is buying.">
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

<!-- Archive with category links -->
<div class="archive">
  <h2>Trend Archive – Explore Past Hot Deals</h2>
  <p style="text-align:center;">
  Browse by category: 
  {% for cat in categories %}
    <a href="/category/{{ cat | lower | replace(' & ', '-and-') | replace(' ', '-') }}" class="category-link">{{ cat }}</a>{% if not loop.last %} | {% endif %}
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

CATEGORY_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FyboBuybo - Archive: {{ category_title }}</title>
<meta name="description" content="Explore all the best {{ category_title }} deals at FyboBuybo. Updated daily with trending products in this category.">
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

@app.route("/")
def home():
    today_products = refresh_products()
    history = load_history()
    archive_dates = sorted([d for d in history.keys() if d != str(datetime.date.today())], reverse=True)
    all_categories = set()
    for date_products in history.values():
        for p in date_products:
            all_categories.add(p["category"])
    categories = sorted(all_categories)

    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)

    return render_template_string(MAIN_HTML, today_products=today_products, archive=history, archive_dates=archive_dates, categories=categories, text_accent=theme["text_accent"], accent=theme["accent"], css=css)

@app.route("/category/<cat_slug>")
def category_page(cat_slug):
    slug_to_title = {
        "electronics": "Electronics",
        "fashion": "Fashion",
        "toys-games": "Toys & Games",
        "beauty": "Beauty",
        "sports-outdoors": "Sports & Outdoors",
        "home-kitchen": "Home & Kitchen",
        "books": "Books",
        "health-personal-care": "Health & Personal Care",
    }

    category_title = slug_to_title.get(cat_slug.lower())
    if not category_title:
        abort(404)

    history = load_history()
    category_products = []
    for date_products in history.values():
        for p in date_products:
            if p["category"] == category_title:
                category_products.append(p)

    if not category_products:
        abort(404)

    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)

    return render_template_string(CATEGORY_HTML, category_products=category_products, category_title=category_title, css=css)

@app.route("/sitemap.xml")
def sitemap():
    history = load_history()
    urls = []

    for date_products in history.values():
        for p in date_products:
            urls.append(f'<url><loc>{p["url"]}</loc></url>')

    return Response(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{"".join(urls)}</urlset>', mimetype='application/xml')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

