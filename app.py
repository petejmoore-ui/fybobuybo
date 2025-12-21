import os
import json
import datetime
import re
from flask import Flask, render_template_string, abort, Response
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "cache.json"
HISTORY_FILE = "history.json"
AFFILIATE_TAG = "whoaccepts-21"
SITE_URL = os.environ.get("SITE_URL", "https://yourdomain.com")

# ---------------- PRODUCTS ---------------- #

PRODUCTS = [
    {
        "name": "VonShef 3 Tray Buffet Server & Hot Plate Food Warmer",
        "category": "Home & Kitchen",
        "image": "https://m.media-amazon.com/images/I/71kTQECp3FL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/VonShef-Tray-Warmer-Buffet-Server/dp/B073Q5G9VX?tag={AFFILIATE_TAG}",
        "info": "A three-tray electric buffet server designed to keep food warm and presentable for entertaining, celebrations, and family meals."
    },
    {
        "name": "Amazon Fire TV Stick 4K",
        "category": "Electronics",
        "image": "https://m.media-amazon.com/images/I/61TzK204IjL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Amazon-Fire-TV-Stick-4K/dp/B08XVYZ1Y5?tag={AFFILIATE_TAG}",
        "info": "A compact streaming device offering smooth 4K playback with voice control and wide app support."
    }
]

# ---------------- THEMES ---------------- #

THEMES = [
    {
        "bg": "#0f172a",
        "card": "#1e293b",
        "accent": "#38bdf8",
        "button": "#0284c7",
        "tag": "#7dd3fc",
        "text_accent": "#bae6fd",
        "gradient": "linear-gradient(90deg,#0284c7,#38bdf8)"
    }
]

def get_daily_theme():
    return THEMES[datetime.date.today().timetuple().tm_yday % len(THEMES)]

# ---------------- AI HOOK ---------------- #

def generate_hook(name):
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"""
Write a calm, elegant 1–2 sentence description explaining why this is a popular UK online product.
Naturally reference popularity and everyday usefulness. Use <b> tags subtly.
No urgency or sales language.
Product: {name}
"""
            }],
            temperature=0.7,
            max_tokens=90
        )
        hook = r.choices[0].message.content.strip()
        hook = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', hook)
        return hook
    except:
        return f"A well-regarded choice among UK shoppers, valued for its thoughtful design and everyday practicality."

# ---------------- STORAGE ---------------- #

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def refresh_products():
    today = str(datetime.date.today())

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            cache = json.load(f)
            if cache.get("date") == today:
                return cache["products"]

    enriched = [{**p, "hook": generate_hook(p["name"])} for p in PRODUCTS]

    with open(CACHE_FILE, "w") as f:
        json.dump({"date": today, "products": enriched}, f)

    history = load_history()
    history[today] = enriched
    save_history(history)

    return enriched

# ---------------- CSS ---------------- #

CSS_TEMPLATE = """
<style>
body{margin:0;background:{{bg}};color:#fff;font-family:'Outfit',sans-serif;padding:20px}
h1{text-align:center;font-size:3rem;background:{{gradient}};-webkit-background-clip:text;color:transparent}
.subtitle{text-align:center;opacity:.85;max-width:900px;margin:20px auto;color:{{text_accent}}}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:22px;max-width:1400px;margin:auto}
.card{background:{{card}};border-radius:22px;padding:18px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.6)}
img{width:100%;border-radius:16px;margin-top:12px}
.tag{background:{{tag}};padding:6px 14px;border-radius:20px;font-size:.85rem}
button{background:{{button}};border:none;padding:14px 34px;border-radius:50px;font-size:1.1rem;font-weight:900;color:white;cursor:pointer}
footer{text-align:center;opacity:.6;margin:60px 0}
a{color:{{text_accent}}}
</style>
"""

# ---------------- HTML ---------------- #

MAIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>FyboBuybo – Trending UK Deals & Popular Products</title>
<meta name="description" content="Discover trending UK deals across electronics, home, toys and more. Updated daily with popular products people are buying right now.">

<meta property="og:title" content="FyboBuybo – Trending UK Deals">
<meta property="og:description" content="Daily-updated UK product trends, seasonal favourites and popular online finds.">
<meta property="og:type" content="website">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">

{{ css|safe }}
</head>
<body>

<h1>FyboBuybo – Trending UK Deals</h1>
<p class="subtitle">A curated look at popular products and online bestsellers, refreshed daily.</p>

<p style="text-align:center;opacity:.7;">
✔ UK-focused · ✔ Updated daily · ✔ Independent curation
</p>

<div class="grid">
{% for p in products %}
<div class="card">
<span class="tag">{{ p.category }}</span>
<h3>{{ p.name }}</h3>

<a href="{{ p.url }}" target="_blank" rel="nofollow">
<img src="{{ p.image }}" alt="{{ p.name }} – popular UK product" loading="lazy">
</a>

<p>{{ p.hook|safe }}</p>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{{ p.name }}",
  "image": "{{ p.image }}",
  "description": "{{ p.info }}",
  "url": "{{ p.url }}"
}
</script>

<a href="{{ p.url }}" target="_blank" rel="nofollow">
<button>View on Amazon</button>
</a>

<p style="font-size:.8rem;opacity:.6;">
More <a href="/category/{{ p.category|lower|replace(' & ','-and-')|replace(' ','-') }}">{{ p.category }}</a> deals
</p>
</div>
{% endfor %}
</div>

<footer>
FyboBuybo is an independent UK deals site. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates.
</footer>
</body>
</html>
"""

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    return render_template_string(MAIN_HTML, products=refresh_products(), css=css)

@app.route("/category/<slug>")
def category(slug):
    history = load_history()
    products = [p for day in history.values() for p in day if slug == p["category"].lower().replace(" & ","-and-").replace(" ","-")]
    if not products:
        abort(404)

    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    return render_template_string(MAIN_HTML, products=products, css=css)

# ---------------- SEO FILES ---------------- #

@app.route("/robots.txt")
def robots():
    return Response(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml",
        mimetype="text/plain"
    )

@app.route("/sitemap.xml")
def sitemap():
    history = load_history()
    urls = {f"{SITE_URL}/"}
    for day in history.values():
        for p in day:
            urls.add(f"{SITE_URL}/category/{p['category'].lower().replace(' & ','-and-').replace(' ','-')}")

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in sorted(urls):
        xml.append(f"<url><loc>{u}</loc></url>")
    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
