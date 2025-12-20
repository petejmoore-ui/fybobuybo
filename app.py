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

PRODUCTS = [
    {
    "name": "VonShef 3 Tray Buffet Server & Hot Plate Food Warmer",
    "category": "Home & Kitchen",
    "image": "https://m.media-amazon.com/images/I/71kTQECp3FL._AC_SX679_.jpg",  # High-res main image
    "url": f"https://www.amazon.co.uk/VonShef-Tray-Warmer-Buffet-Server/dp/B073Q5G9VX?tag={AFFILIATE_TAG}",
    "info": "3-tray electric buffet server with adjustable temperature — keeps food warm for parties, hosting, or family meals. Top trending choice for holiday entertaining with easy clean trays."
},

{
    "name": "Driving Theory Test Kit UK 2025 with Highway Code Book",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/81akIVih9NL._SY385_.jpg",  # Right-click main photo on Amazon page → Copy image address → use high-res _SL1500_.jpg version
    "url": f"https://www.amazon.co.uk/UK-Driving-Theory-Test-Kit/dp/B09D84M7C4?tag={AFFILIATE_TAG}",
    "info": "Complete 2025 theory test kit with official Highway Code book, practice questions, hazard perception — essential for passing the UK driving test. Massive demand spike for new learners."
},

{
    "name": "Magnetic Chess Game with Stones Portable Family Board",
    "category": "Toys & Games",
    "image": "https://m.media-amazon.com/images/I/61mcbNi2MGL._AC_SX679_.jpg",  # High-res main image (right-click on Amazon page if needed for exact)
    "url": f"https://www.amazon.co.uk/Magnetic-Training-Chesss-Birthdays-Gatherings/dp/B0FMXLG87Y?tag={AFFILIATE_TAG}",
    "info": "Portable magnetic chess set with stones and ropes — fun family game for parties, travel, or gatherings. Addictive strategy challenge that's trending for all ages."
},

{
    "name": "Magnesium Glycinate 3-in-1 Complex 1800mg Capsules",
    "category": "Health & Personal Care",
    "image": "https://m.media-amazon.com/images/I/717wIpxmJdL._AC_SX679_.jpg",  # High-res main image (tested from similar listings; right-click on page for exact if needed)
    "url": f"https://www.amazon.co.uk/Magnesium-Glycinate-Complex-Supplements-Bisglycinate/dp/B0C9VVCL12?tag={AFFILIATE_TAG}",
    "info": "High-absorption 3-in-1 magnesium (glycinate, citrate, malate) — supports sleep, muscle recovery, energy, and stress relief. Consistent bestseller for wellness routines."
},
    {"name": "[Built-in Apps & Android 11.0] Mini Projector Portable 20000 Lux 4K Supported", "category": "Electronics", 
     "image": "https://m.media-amazon.com/images/I/61FJ2edQURL._AC_SY300_SX300_QL70_ML2_.jpg",
     "url": f"https://www.amazon.co.uk/Projector-Portable-Supported-Rotation-Compatible/dp/B0FMR73KL2?tag={AFFILIATE_TAG}",
     "info": "Compact portable projector with Android 11, built-in apps, 180° rotation, auto keystone — perfect for home cinema, outdoor movies, or gaming. High brightness and compatibility make it a top trending choice."},
    {"name": "Gezqieunk Christmas Jumper Women Xmas Printed Sweatshirt", "category": "Fashion", 
     "image": "https://m.media-amazon.com/images/I/61Tm7Sqg13L._AC_SX679_.jpg",
     "url": f"https://www.amazon.co.uk/Gezqieunk-Christmas-Sweatshirts-Crewneck-Sweaters/dp/B0FXF94VW8?tag={AFFILIATE_TAG}",
     "info": "Festive oversized jumper with fun Christmas prints — perfect cosy gift, surging in popularity for holiday parties and family photos."},
    {"name": "Karaoke Machine for Kids with Microphone", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81QJgWZmfyL._AC_SX679_.jpg",
     "url": f"https://www.amazon.co.uk/Kids-Karaoke-Machine-Birthday-Girls-Pink/dp/B0DK4NL37F?tag={AFFILIATE_TAG}",
     "info": "Mini karaoke set with lights, Bluetooth, and mic — top Christmas gift for kids, massive sales spike for family sing-alongs."},
    {"name": "L’Oréal Paris Revitalift Laser Anti-Ageing Day Cream", "category": "Beauty", 
     "image": "https://m.media-amazon.com/images/I/41uhhU1DU7L._AC_SY300_SX300_QL70_ML2_.jpg",
     "url": f"https://www.amazon.co.uk/LOreal-Paris-Revitalift-Pro-Xylane-Anti-Ageing/dp/B00SNOAZM8?tag={AFFILIATE_TAG}",
     "info": "Triple-action cream reduces wrinkles and firms skin — huge mover in beauty for gifting season and self-care routines."},
    {"name": "OCOOPA Magnetic Hand Warmers Rechargeable 2 Pack", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/61sa5Gx+ZQL._AC_SY300_SX300_QL70_ML2_.jpg",
     "url": f"https://www.amazon.co.uk/OCOOPA-Magnetic-Rechargeable-Handwarmers-Certified/dp/B0CH34CB3P?tag={AFFILIATE_TAG}",
     "info": "Portable, double-sided heat with magnetic design — essential for cold UK winter walks, commuters, and outdoor events."},
    {"name": "Herd Mentality Board Game", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/61jvW6xtkdL._AC_SY300_SX300_QL70_ML2_.jpg",
     "url": f"https://www.amazon.co.uk/Herd-Mentality-Board-Game-Addictive/dp/B09S3YBBRR?tag={AFFILIATE_TAG}",
     "info": "Hilarious party game where you try to think like the herd — perfect family/party entertainment, flying off shelves for Christmas."},
    {"name": "Amazon Fire TV Stick 4K", "category": "Electronics", 
     "image": "https://m.media-amazon.com/images/I/61TzK204IjL._AC_SX679_.jpg",
     "url": f"https://www.amazon.co.uk/Amazon-Fire-TV-Stick-4K/dp/B08XVYZ1Y5?tag={AFFILIATE_TAG}",
     "info": "Stream 4K content with Dolby Vision and Alexa voice control — top gift for movie lovers and home entertainment upgrades."},
]

# 6 Daily Rotating Themes
THEMES = [
    { "bg": "#0d0d1f", "card": "#161630", "accent": "#ff4e4e", "button": "#ff4e4e", "tag": "#8b5cf6", "text_accent": "#ff6b6b", "gradient": "linear-gradient(90deg,#ff4e4e,#8b5cf6)" },
    { "bg": "#0f172a", "card": "#1e293b", "accent": "#60a5fa", "button": "#3b82f6", "tag": "#93c5fd", "text_accent": "#93c5fd", "gradient": "linear-gradient(90deg,#3b82f6,#60a5fa)" },
    { "bg": "#111827", "card": "#1f2937", "accent": "#ef4444", "button": "#dc2626", "tag": "#22c55e", "text_accent": "#22c55e", "gradient": "linear-gradient(90deg,#dc2626,#22c55e)" },
    { "bg": "#0f172a", "card": "#164e63", "accent": "#06b6d4", "button": "#0891b2", "tag": "#22d3ee", "text_accent": "#67e8f9", "gradient": "linear-gradient(90deg,#0891b2,#22d3ee)" },
    { "bg": "#1e1b4b", "card": "#312e81", "accent": "#f97316", "button": "#ea580c", "tag": "#fb923c", "text_accent": "#fdba74", "gradient": "linear-gradient(90deg,#ea580c,#f97316)" },
    { "bg": "#022c22", "card": "#065f46", "accent": "#10b981", "button": "#059669", "tag": "#34d399", "text_accent": "#6ee7b7", "gradient": "linear-gradient(90deg,#059669,#34d399)" }
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
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;max-width:1400px;margin:auto}
.card{background:{{card}};border-radius:22px;padding:22px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.6);transition:.3s}
.card:hover{transform:scale(1.05)}
img{width:100%;border-radius:16px;transition:0.3s}
.card a img:hover{opacity:0.9;transform:scale(1.03)}
.tag{background:{{tag}};padding:6px 14px;border-radius:20px;font-size:.85rem;display:inline-block;margin-bottom:10px}
button{background:{{button}};border:none;padding:14px 36px;border-radius:50px;font-size:1.2rem;font-weight:900;color:white;cursor:pointer}
.hook{margin:14px 0;line-height:1.5}
footer{text-align:center;opacity:.6;margin:60px 0}

/* Big "Read More" button */
details {margin-top:16px;}
details summary {font-weight:900;font-size:1.1rem;color:{{accent}};cursor:pointer;display:inline-block;padding:10px 20px;background:{{card}};border:2px solid {{accent}};border-radius:50px;transition:0.3s;}
details summary:hover {background:{{accent}};color:white;}
details[open] summary {border-radius:50px 50px 0 0;}
details p {background:{{card}};padding:16px;border-radius:0 0 16px 16px;border:2px solid {{accent}};border-top:none;margin:0;font-size:0.9rem;opacity:0.9;}

/* Archive styling */
.archive {margin-top:80px;}
.archive h2 {text-align:center;color:{{accent}};font-size:2rem;margin-bottom:40px;}
.archive details {margin-bottom:20px;}
.archive summary {font-size:1.5rem;cursor:pointer;color:{{text_accent}};}
.archive .category-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;margin-top:20px;}
.category-link {color:{{text_accent}};text-decoration:underline;cursor:pointer;margin:10px;display:inline-block;}
</style>
"""

MAIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FyboBuybo</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">
{{ css | safe }}
</head>
<body>
<h1>FyboBuybo</h1>
<p class="subtitle">Discover the hottest UK deals right now — from seasonal gifts and essentials to viral gadgets everyone's buying. Updated daily with what's trending!</p>

<h2>Today's Trending Deals</h2>
<div class="grid">
{% for p in today_products %}
<div class="card">
  <span class="tag">{{ p.category }}</span>
  <a href="{{ p.url }}" target="_blank">
    <img src="{{ p.image }}" alt="{{ p.name }}">
  </a>
  <h3>{{ p.name }}</h3>
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
      <a href="/category/{{ cat|lower|replace(' & ', '-')|replace(' ', '-') }}" class="category-link">{{ cat }}</a>{% if not loop.last %} | {% endif %}
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
            <a href="{{ p.url }}" target="_blank">
              <img src="{{ p.image }}" alt="{{ p.name }}">
            </a>
            <h3>{{ p.name }}</h3>
            <div class="hook">{{ p.hook|safe }}</div>
            <a href="{{ p.url }}" target="_blank">
              <button>Grab It Now 🔥</button>
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
  <a href="{{ p.url }}" target="_blank">
    <img src="{{ p.image }}" alt="{{ p.name }}">
  </a>
  <h3>{{ p.name }}</h3>
  <div class="hook">{{ p.hook|safe }}</div>
  <details>
    <summary>Read More ↓</summary>
    <p>{{ p.info }}</p>
  </details>
  <a href="{{ p.url }}" target="_blank">
    <button>Grab It Now 🔥</button>
  </a>
</div>
{% endfor %}
</div>

<footer>Affiliate links may earn commission · Made with AI</footer>
</body>
</html>
"""

def generate_hook(name):
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"Create a unique, exciting 1-2 sentence sales hook starting with the product name '{name}'. Make it relevant to the product's appeal, use <b> tags for bold emphasis (no **), vary the style, and end with a natural call to action like 'Perfect for gifting!' or 'Add to basket today!'"
            }],
            temperature=1.0,
            max_tokens=90
        )
        return r.choices[0].message.content
    except Exception as e:
        print(f"Groq error: {e}")
        return f"<b>{name}</b> is a popular choice this season.<br>Perfect for your basket!"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def refresh_products():
    today = str(datetime.date.today() + datetime.timedelta(days=1))  # Forces "tomorrow"
    today_products = []

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            data = json.load(f)
            if data.get("date") == today:
                today_products = data["products"]

    if not today_products:
        enriched = []
        for p in PRODUCTS:
            enriched.append({**p, "hook": generate_hook(p["name"])})
        today_products = enriched

        with open(CACHE_FILE, "w") as f:
            json.dump({"date": today, "products": today_products}, f)

        history = load_history()
        history[today] = today_products
        save_history(history)

    return today_products

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

    return render_template_string(MAIN_HTML, today_products=today_products, archive=history, archive_dates=archive_dates, categories=categories, text_accent=theme["text_accent"], css=css)

@app.route("/category/<cat_slug>")
def category_page(cat_slug):
    # Convert slug back to title (e.g., "toys-games" -> "Toys & Games")
    category_title = cat_slug.replace('-', ' ').title()
    if ' & ' in category_title:
        category_title = category_title.replace(' & ', ' & ')

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
