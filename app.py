import os
import json
import datetime
import re
from flask import Flask, render_template_string, abort, Response, request
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "cache.json"
HISTORY_FILE = "history.json"
AFFILIATE_TAG = "whoaccepts-21"
SITE_URL = os.environ.get("SITE_URL", "https://yourdomain.com").rstrip("/")

# ---------------- PRODUCTS ---------------- #

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
    {
        "name": "Magnesium Glycinate 3-in-1 Complex 1800mg Capsules",
        "category": "Health & Personal Care",
        "image": "https://m.media-amazon.com/images/I/717wIpxmJdL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Magnesium-Glycinate-Complex-Supplements-Bisglycinate/dp/B0C9VVCL12?tag={AFFILIATE_TAG}",
        "info": "High-absorption 3-in-1 magnesium (glycinate, citrate, malate) — supports sleep, muscle recovery, energy, and stress relief. Consistent bestseller for wellness routines."
    },
    {
        "name": "[Built-in Apps & Android 11.0] Mini Projector Portable 20000 Lux 4K Supported",
        "category": "Electronics",
        "image": "https://m.media-amazon.com/images/I/61FJ2edQURL._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/Projector-Portable-Supported-Rotation-Compatible/dp/B0FMR73KL2?tag={AFFILIATE_TAG}",
        "info": "Compact portable projector with Android 11, built-in apps, 180° rotation, auto keystone — perfect for home cinema, outdoor movies, or gaming. High brightness and compatibility make it a top trending choice."
    },
    {
        "name": "Gezqieunk Christmas Jumper Women Xmas Printed Sweatshirt",
        "category": "Fashion",
        "image": "https://m.media-amazon.com/images/I/61Tm7Sqg13L._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Gezqieunk-Christmas-Sweatshirts-Crewneck-Sweaters/dp/B0FXF94VW8?tag={AFFILIATE_TAG}",
        "info": "Festive oversized jumper with fun Christmas prints — perfect cosy gift, surging in popularity for holiday parties and family photos."
    },
    {
        "name": "Karaoke Machine for Kids with Microphone",
        "category": "Toys & Games",
        "image": "https://m.media-amazon.com/images/I/81QJgWZmfyL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Kids-Karaoke-Machine-Birthday-Girls-Pink/dp/B0DK4NL37F?tag={AFFILIATE_TAG}",
        "info": "Mini karaoke set with lights, Bluetooth, and mic — top Christmas gift for kids, massive sales spike for family sing-alongs."
    },
    {
        "name": "L’Oréal Paris Revitalift Laser Anti-Ageing Day Cream",
        "category": "Beauty",
        "image": "https://m.media-amazon.com/images/I/41uhhU1DU7L._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/LOreal-Paris-Revitalift-Pro-Xylane-Anti-Ageing/dp/B00SNOAZM8?tag={AFFILIATE_TAG}",
        "info": "Triple-action cream reduces wrinkles and firms skin — huge mover in beauty for gifting season and self-care routines."
    },
    {
        "name": "OCOOPA Magnetic Hand Warmers Rechargeable 2 Pack",
        "category": "Sports & Outdoors",
        "image": "https://m.media-amazon.com/images/I/61sa5Gx+ZQL._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/OCOOPA-Magnetic-Rechargeable-Handwarmers-Certified/dp/B0CH34CB3P?tag={AFFILIATE_TAG}",
        "info": "Portable, double-sided heat with magnetic design — essential for cold UK winter walks, commuters, and outdoor events."
    },
    {
        "name": "Herd Mentality Board Game",
        "category": "Toys & Games",
        "image": "https://m.media-amazon.com/images/I/61jvW6xtkdL._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/Herd-Mentality-Board-Game-Addictive/dp/B09S3YBBRR?tag={AFFILIATE_TAG}",
        "info": "Hilarious party game where you try to think like the herd — perfect family/party entertainment, flying off shelves for Christmas."
    },
    {
        "name": "Amazon Fire TV Stick 4K",
        "category": "Electronics",
        "image": "https://m.media-amazon.com/images/I/61TzK204IjL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Amazon-Fire-TV-Stick-4K/dp/B08XVYZ1Y5?tag={AFFILIATE_TAG}",
        "info": "Stream 4K content with Dolby Vision and Alexa voice control — top gift for movie lovers and home entertainment upgrades."
    },
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
Naturally reference everyday usefulness and popularity.
Use <b> tags subtly. No urgency or sales language.
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
        return "A well-regarded product among UK shoppers, valued for its thoughtful design and everyday practicality."

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

# ---------------- HELPERS ---------------- #

def slugify(text):
    text = text.lower()
    text = re.sub(r'&', '-and-', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    return text

def get_categories(history):
    return sorted({p["category"] for day in history.values() for p in day})

# ---------------- CSS (enhanced with hover effects) ---------------- #

CSS_TEMPLATE = """
<style>
body{margin:0;background:{{bg}};color:#fff;font-family:'Outfit',sans-serif;padding:20px 20px 40px}
h1{text-align:center;font-size:3rem;background:{{gradient}};-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:40px 0 10px}
.subtitle{text-align:center;opacity:.85;max-width:900px;margin:20px auto;color:{{text_accent}};font-size:1.1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;max-width:1400px;margin:auto}
.card{background:{{card}};border-radius:22px;padding:20px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.6);transition:transform .3s,box-shadow .3s}
.card:hover{transform:translateY(-8px);box-shadow:0 30px 60px rgba(0,0,0,.7)}
img{width:100%;border-radius:16px;margin:16px 0}
.tag{background:{{tag}};padding:6px 14px;border-radius:20px;font-size:.85rem;display:inline-block;margin-bottom:12px}
button{background:{{button}};border:none;padding:16px 36px;border-radius:50px;font-size:1.1rem;font-weight:900;color:white;cursor:pointer;transition:.3s}
button:hover{opacity:.9;transform:scale(1.05)}
footer{text-align:center;opacity:.7;margin:80px 0 40px;font-size:.9rem;line-height:1.6}
a{color:{{text_accent}};text-decoration:none}
nav{background:{{card}};padding:16px;margin:20px 0 40px;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.4);text-align:center}
nav a{margin:0 16px;color:{{text_accent}};font-weight:700;font-size:1.1rem;transition:.2s}
nav a:hover{opacity:.8}
@media (max-width:768px){
    nav a{margin:0 10px;font-size:1rem}
    .grid{grid-template-columns:1fr}
}
</style>
"""

# ---------------- HTML TEMPLATE ---------------- #

BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>{{ title }}</title>
<meta name="description" content="{{ description }}">
<link rel="canonical" href="{{ canonical_url }}">

<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ description }}">
<meta property="og:type" content="website">
<meta property="og:url" content="{{ canonical_url }}">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">

{{ css|safe }}
</head>
<body>

<nav>
    <a href="/">Home</a>
    <a href="/best-uk-deals">All Deals</a>
    <a href="/archive">Archive</a>
    {% for cat in categories %}
    <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
    {% endfor %}
</nav>

<h1>{{ heading }}</h1>
<p class="subtitle">{{ subtitle }}</p>

<p style="text-align:center;opacity:.7;margin-bottom:40px;">
✔ UK-focused · ✔ Updated daily · ✔ Independent curation
</p>

<div class="grid">
{% for p in products %}
<div class="card">
    <span class="tag">{{ p.category }}</span>
    <h2>{{ p.name }}</h2>

    <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored">
        <img src="{{ p.image }}" alt="{{ p.name }} – {{ p.info[:120] }}{% if p.info|length > 120 %}...{% endif %}" loading="lazy">
    </a>

    <p>{{ p.hook|safe }}</p>

    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Product",
      "name": "{{ p.name }}",
      "image": "{{ p.image }}",
      "description": "{{ p.info }}",
      "url": "{{ p.url }}",
      "offers": {
        "@type": "Offer",
        "url": "{{ p.url }}",
        "priceCurrency": "GBP",
        "availability": "https://schema.org/InStock",
        "seller": {
          "@type": "Organization",
          "name": "Amazon"
        }
      }
    }
    </script>

    <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored" aria-label="View {{ p.name }} on Amazon">
        <button>View on Amazon</button>
    </a>

    <p style="font-size:.85rem;opacity:.7;margin-top:16px;">
        More <a href="/category/{{ slugify(p.category) }}">{{ p.category }}</a> deals
    </p>
</div>
{% endfor %}
</div>

<footer>
    <p><strong>As an Amazon Associate, I earn from qualifying purchases.</strong></p>
    <p>FyboBuybo is an independent UK deals site. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates.</p>
</footer>

</body>
</html>
"""

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    products = refresh_products()
    history = load_history()
    categories = get_categories(history)
    canonical = SITE_URL + "/"

    return render_template_string(
        BASE_HTML,
        title="FyboBuybo – Trending UK Deals & Popular Products",
        description="Discover today's trending UK deals and popular products across electronics, home, toys, beauty and more. Independently curated and refreshed daily.",
        heading="FyboBuybo – Trending UK Deals",
        subtitle="A curated look at popular products and online bestsellers, refreshed daily.",
        products=products,
        categories=categories,
        css=css,
        canonical_url=canonical,
        slugify=slugify
    )

@app.route("/category/<slug>")
def category(slug):
    history = load_history()
    products = [p for day in history.values() for p in day if slugify(p["category"]) == slug]
    if not products:
        abort(404)

    cat_name = products[0]["category"]
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    categories = get_categories(history)
    canonical = SITE_URL + request.path

    return render_template_string(
        BASE_HTML,
        title=f"{cat_name} Deals – FyboBuybo",
        description=f"Explore popular and trending {cat_name} products in the UK, featuring bestsellers and well-reviewed items.",
        heading=f"{cat_name} Deals",
        subtitle=f"Hand-picked popular products in {cat_name}, updated from our daily selections.",
        products=products,
        categories=categories,
        css=css,
        canonical_url=canonical,
        slugify=slugify
    )

@app.route("/archive")
def archive():
    history = load_history()
    products = [p for day in history.values() for p in day]
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    categories = get_categories(history)
    canonical = SITE_URL + "/archive"

    return render_template_string(
        BASE_HTML,
        title="Deal Archive – FyboBuybo",
        description="Browse our full archive of previously featured trending UK deals and popular products.",
        heading="Deal Archive",
        subtitle="All previously featured popular products across every category.",
        products=products,
        categories=categories,
        css=css,
        canonical_url=canonical,
        slugify=slugify
    )

@app.route("/best-uk-deals")
def long_tail():
    history = load_history()
    products = [p for day in history.values() for p in day]
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    categories = get_categories(history)
    canonical = SITE_URL + "/best-uk-deals"

    return render_template_string(
        BASE_HTML,
        title="Best UK Deals – Popular Products Right Now",
        description="A broader selection of the best UK deals and most popular products people are buying online today.",
        heading="Best UK Deals",
        subtitle="Popular and well-reviewed products across all categories.",
        products=products,
        categories=categories,
        css=css,
        canonical_url=canonical,
        slugify=slugify
    )

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
    urls = {
        f"{SITE_URL}/",
        f"{SITE_URL}/archive",
        f"{SITE_URL}/best-uk-deals"
    }
    for cat in get_categories(history):
        urls.add(f"{SITE_URL}/category/{slugify(cat)}")

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in sorted(urls):
        xml.append(f"<url><loc>{u}</loc></url>")
    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
