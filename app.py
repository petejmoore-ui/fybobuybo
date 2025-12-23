import os
import json
import datetime
import re
from flask import Flask, render_template_string, abort, Response, request, url_for
from groq import Groq
from dotenv import load_dotenv
from threading import Thread

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "/data/cache.json"
HISTORY_FILE = "/data/history.json"
AFFILIATE_TAG = "whoaccepts-21"
SITE_URL = "https://fybobuybo.com"
ITEMS_PER_PAGE = 12

# ---------------- PRODUCTS ---------------- #
PRODUCTS = [
    {
        "name": "The Impossible Fortune by Richard Osman (Thursday Murder Club 5)",
        "category": "Books",
        "image": "https://m.media-amazon.com/images/I/71eTwnmHa3L._SY466_.jpg",
        "url": f"https://www.amazon.co.uk/Impossible-Fortune-multi-million-bestselling-Thursday/dp/0241743982?tag={AFFILIATE_TAG}",
        "info": "The latest cosy crime bestseller in the multi-million selling Thursday Murder Club series — perfect for fans of clever, heartwarming murder mysteries."
    },
    {
        "name": "Catsan Hygiene Plus Non-Clumping Cat Litter, 100% Natural White Hygiene Granules, Odour Control, 20 L",
        "category": "Pet Supplies",
        "image": "https://m.media-amazon.com/images/I/71bURZaHfFL._AC_SX425_.jpg",
        "url": f"https://www.amazon.co.uk/Catsan-Hygiene-Plus-Litter-White/dp/B001MZV3OO?tag={AFFILIATE_TAG}",
        "info": "Non-clumping white hygiene cat litter made from natural quartz sand and lime — highly absorbent, locks in odours, and prevents bacterial growth for superior freshness. UK's leading choice for clean, hygienic litter trays and happy cats."
    },
    {
        "name": "HotHands Hand Warmers - Up to 10 Hours of Heat - 40 Pairs - Air Activated, Odourless, Natural & Safe",
        "category": "Sports & Outdoors",
        "image": "https://m.media-amazon.com/images/I/71SBcNUrFCL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/HOTHANDS-Hand-Warmers-Pairs-activated/dp/B08GCT8SXZ?tag={AFFILIATE_TAG}",
        "info": "Air-activated hand warmers providing up to 10 hours of natural, odourless heat — safe, easy to use, and perfect for cold weather activities, commuting, or outdoor events. Bestselling essential for staying warm during winter walks, sports, or festivals."
    },
    {
        "name": "Fitbit Charge 6 Activity Tracker with 6 months of Fitbit Premium Included, Heart Rate, GPS, Health Tools, Sleep Tracking, Readiness Score and More - Obsidian/Black",
        "category": "Sports & Outdoors",
        "image": "https://m.media-amazon.com/images/I/61AeGQhwjxL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Fitbit-Activity-6-months-Membership-Readiness/dp/B0B6WRFY5S?tag={AFFILIATE_TAG}",
        "info": "Advanced fitness tracker with built-in GPS, heart rate monitoring, sleep tracking, stress management, and a daily Readiness Score — includes 6 months Premium membership. Popular choice for active lifestyles, workout motivation, and overall health insights in everyday routines."
    },
    {
        "name": "WaterWipes Sensitive+ Newborn & Baby Wipes, 720 Count (12 Packs), 3-In-1 Cleans, Cares, Protects, 99.9% Water, Unscented",
        "category": "Baby",
        "image": "https://m.media-amazon.com/images/I/81OT3srjQiL._AC_SX679_PIbundle-12,TopRight,0,0_SH20_.jpg",
        "url": f"https://www.amazon.co.uk/WaterWipes-Sensitive-Newborn-Biodegradable-Unscented/dp/B08MXSBRSB?tag={AFFILIATE_TAG}",
        "info": "Gentle baby wipes made with 99.9% purified water and a drop of fruit extract — plastic-free, unscented, and dermatologist-approved for sensitive newborn skin, including eczema-prone. UK's top choice for pure, effective cleansing that cares for and protects delicate skin every day."
    },
    {
        "name": "Mens Two Tone Memory Foam Slippers Mule Slip On Comfortable Hard Sole Non Slip Slippers for Men",
        "category": "Fashion",
        "image": "https://m.media-amazon.com/images/I/81EEfuhlShL._AC_SY695_.jpg",
        "url": f"https://www.amazon.co.uk/Mens-Two-Tone-Memory-Foam-Slipper/dp/B07CLXD2V4?tag={AFFILIATE_TAG}",
        "info": "Cosy two-tone memory foam slippers with hard non-slip sole and mule design — perfect for indoor comfort and quick outdoor trips. Bestselling men's slippers for all-day warmth, support, and durability during colder months."
    },
    {
        "name": "More or Less: The Game of Judgement & Outlandish Guesstimation",
        "category": "Toys & Games",
        "image": "https://m.media-amazon.com/images/I/71i5j54tKVL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/More-Less-Judgement-Outlandish-Guesstimation/dp/B087KLKN7T?tag={AFFILIATE_TAG}",
        "info": "Hilarious party game where players guess whether random facts are 'more' or 'less' than a given number — perfect for family gatherings, parties, and game nights. Trending for its mix of ridiculous questions, laughs, and surprising knowledge."
    },
    {
        "name": "Catching Sticks Games, Falling Sticks Catching Game, Drop It Catch It Win It Reaction Game",
        "category": "Toys & Games",
        "image": "https://m.media-amazon.com/images/I/71dAXELqizL._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/Catching-Reaction-Reactions-Coordination-Christmas/dp/B0FMD3DXPC?tag={AFFILIATE_TAG}",
        "info": "Fast-paced reaction game where colorful sticks drop randomly at adjustable speeds — players race to catch them, building hand-eye coordination and quick reflexes. Viral trending Christmas gift for kids and families, perfect for parties and screen-free fun."
    },
    {
        "name": "WOQQW Back Massager with Heat, Shiatsu Back and Neck Massager, Deeper Tissue Kneading Massage Pillow for Shoulder, Leg, Foot, Body",
        "category": "Health & Personal Care",
        "image": "https://m.media-amazon.com/images/I/81fiFvLzZ1L._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/Massager-Shiatsu-Kneading-Massage-Shoulder/dp/B08MYSL6T8?tag={AFFILIATE_TAG}",
        "info": "Shiatsu massage pillow with deep-kneading nodes and soothing heat function — versatile for neck, back, shoulders, legs, and feet to relieve muscle tension and promote relaxation. Popular wellness gift for stress relief during the holiday season and beyond."
    },
    {
        "name": "SHOKZ OpenFit Air Open-Ear Headphones, True Wireless Bluetooth Earphones with Mic, Fast Charging, 28h Playtime, IP54 Waterproof for Workout - Black",
        "category": "Electronics",
        "image": "https://m.media-amazon.com/images/I/61eNpp4eTlL._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/SHOKZ-Headphones-Bluetooth-Earphones-Waterproof-Black/dp/B0CRTM6B55?tag={AFFILIATE_TAG}",
        "info": "Open-ear true wireless headphones with secure fit, situational awareness, powerful bass, and long battery life — ideal for workouts, running, or daily use without blocking ambient sound. Trending choice for active lifestyles and safer outdoor listening."
    },
    {
        "name": "Shot in the Dark: The Ultimate Unorthodox Quiz Game",
        "category": "Toys & Games",
        "image": "https://m.media-amazon.com/images/I/71BXgJpJ0oL._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/Shot-Dark-Christmas-Ultimate-Unorthodox/dp/B08LFY1F42?tag={AFFILIATE_TAG}",
        "info": "Hilarious card-based quiz game with bizarre, obscure questions where nobody knows the answer — players guess, and the best (or funniest) guess wins points. Perfect screen-free entertainment for Christmas parties, family gatherings, and game nights with all ages."
    },
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

# ---------------- IMPROVED AI HOOK ---------------- #
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
End with a complete sentence.
Product: {name}
"""
            }],
            temperature=0.5,
            max_tokens=120
        )
        hook = r.choices[0].message.content.strip()
        hook = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', hook)
        if not re.search(r'[.!?]$', hook):
            hook += " among UK shoppers."
        return hook
    except Exception as e:
        print(f"Groq error: {e}")
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

def enrich_products(products):
    enriched = []
    for p in products:
        p_copy = dict(p)
        p_copy["hook"] = generate_hook(p["name"])
        enriched.append(p_copy)
    return enriched

def refresh_products(background=False):
    today = str(datetime.date.today())
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            cache = json.load(f)
            if cache.get("date") == today:
                return cache["products"]

    def do_refresh():
        enriched = enrich_products(PRODUCTS)
        with open(CACHE_FILE, "w") as f:
            json.dump({"date": today, "products": enriched}, f)
        history = load_history()
        history[today] = enriched
        save_history(history)

    if background:
        Thread(target=do_refresh).start()
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as f:
                cached = json.load(f).get("products", [])
                if cached:
                    return cached
        return [{"name": p["name"], "category": p["category"], "image": p["image"],
                 "url": p["url"], "info": p["info"], "hook": p["info"]} for p in PRODUCTS]
    else:
        do_refresh()
        with open(CACHE_FILE) as f:
            return json.load(f)["products"]

# ---------------- HELPERS ---------------- #
def slugify(text):
    text = text.lower()
    text = re.sub(r'&', '-and-', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    return text

def get_categories(history):
    return sorted({p["category"] for day in history.values() for p in day})

def paginate(items, page):
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return items[start:end], len(items)

def shorten_product_name(name, max_length=120):
    """Shorten long product names intelligently while keeping key info."""
    if len(name) <= max_length:
        return name
    
    if ',' in name:
        shortened = name.split(',', 1)[0].strip()
        if len(shortened) <= max_length:
            return shortened
    
    if '(' in name:
        shortened = name.split('(', 1)[0].strip()
        if len(shortened) <= max_length:
            return shortened
    
    words = name.split()
    shortened = ''
    for word in words:
        if len(shortened + ' ' + word) <= max_length - 3:
            shortened += (' ' + word) if shortened else word
        else:
            break
    return shortened + '...'

# ---------------- CSS ---------------- #
CSS_TEMPLATE = """<style>
body{margin:0;background:{{bg}};color:#fff;font-family:'Outfit',sans-serif;padding:20px 20px 40px}
h1{text-align:center;font-size:3rem;background:{{gradient}};-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:40px 0 10px}
.subtitle{text-align:center;opacity:.85;max-width:900px;margin:20px auto;color:{{text_accent}};font-size:1.1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;max-width:1400px;margin:auto}
.card{background:{{card}};border-radius:22px;padding:20px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.6);transition:transform .3s,box-shadow .3s}
.card:hover{transform:translateY(-8px);box-shadow:0 30px 60px rgba(0,0,0,.7)}
img{width:100%;border-radius:16px;margin:16px 0}
.tag{background:{{tag}};padding:6px 14px;border-radius:20px;font-size:.85rem;display:inline-block;margin-bottom:12px}
button{
    background:{{button}};
    border:none;
    padding:16px 36px;
    border-radius:50px;
    font-size:1.1rem;
    font-weight:900;
    color:white;
    cursor:pointer;
    transition:.3s;
    animation: pulse 2.5s infinite ease-in-out;
}
button:hover{
    opacity:.9;
    transform:scale(1.05);
    animation:none;
}
@keyframes pulse{
    0%{box-shadow:0 0 0 0 rgba(2,132,199,0.4);}
    70%{box-shadow:0 0 0 12px rgba(2,132,199,0);}
    100%{box-shadow:0 0 0 0 rgba(2,132,199,0);}
}
@media (prefers-reduced-motion: reduce){
    button{animation:none;}
}
footer{text-align:center;opacity:.7;margin:80px 0 40px;font-size:.9rem;line-height:1.6}
a{color:{{text_accent}};text-decoration:none}
nav{background:{{card}};padding:16px;margin:20px 0 40px;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.4);text-align:center}
nav a{margin:0 16px;color:{{text_accent}};font-weight:700;font-size:1.1rem;transition:.2s}
nav a:hover{opacity:.8}
.pagination{display:flex;justify-content:center;gap:16px;margin:40px 0}
.pagination a{background:{{button}};padding:10px 16px;border-radius:12px;color:white;text-decoration:none;font-weight:700;transition:.2s}
.pagination a:hover{opacity:.9}
.loading{text-align:center;opacity:.8;margin:80px 0;font-size:1.3rem;color:{{text_accent}};}
@media (max-width:768px){
    nav a{margin:0 10px;font-size:1rem}
    .grid{grid-template-columns:1fr}
}
</style>"""

# ---------------- HTML TEMPLATE ---------------- #
BASE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="google-site-verification" content="ZDatY7MyS9eDAYQB97mQ_dxlAv2dgd2IqG1kPg82imU" />
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title>
<meta name="description" content="{{ description }}">
<link rel="canonical" href="{{ canonical_url }}">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-C1YNKZS6PG"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-C1YNKZS6PG');
</script>
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
    <a href="/all-deals">All Deals</a>
    {% for cat in categories %}
    <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
    {% endfor %}
</nav>

<h1>{{ heading }}</h1>
<p class="subtitle">{{ subtitle }}</p>

<p style="text-align:center;opacity:.7;margin-bottom:40px;">
✔ UK-focused · ✔ Updated daily · ✔ Independent curation
</p>

{% if products %}
<div class="grid">
{% for p in products %}
<div class="card">
    <span class="tag">{{ p.category }}</span>
    <h2>{{ shorten_product_name(p.name) }}</h2>

    <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored">
        <img src="{{ p.image }}" alt="{{ p.name }} – {{ p.info }}" loading="lazy">
    </a>

    <p>{{ p.hook|safe }}</p>

    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Product",
      "name": "{{ shorten_product_name(p.name) }}",
      "image": "{{ p.image }}",
      "description": "{{ p.info }}",
      "url": "{{ p.url }}",
      "brand": {"@type": "Brand", "name": "Various"},
      "offers": {
        "@type": "Offer",
        "url": "{{ p.url }}",
        "priceCurrency": "GBP",
        "price": "0.00",
        "priceValidUntil": "2026-12-31",
        "availability": "https://schema.org/InStock",
        "hasMerchantReturnPolicy": {
          "@type": "MerchantReturnPolicy",
          "applicableCountry": "GB",
          "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
          "merchantReturnDays": 30
        },
        "shippingDetails": {
          "@type": "OfferShippingDetails",
          "shippingRate": {"@type": "MonetaryAmount", "value": "0.00", "currency": "GBP"},
          "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "GB"}
        },
        "seller": {"@type": "Organization", "name": "Amazon"}
      }
    }
    </script>

    <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored" 
       aria-label="View {{ p.name }} on Amazon"
       onclick="gtag('event', 'affiliate_click', { 
           'event_category': '{{ p.category }}', 
           'event_label': '{{ p.name }}', 
           'value': 1,
           'page_path': window.location.pathname
       });">
        <button>View on Amazon</button>
    </a>

    <p style="font-size:.85rem;opacity:.7;margin-top:16px;">
        More <a href="/category/{{ slugify(p.category) }}">{{ p.category }}</a> deals
    </p>
</div>
{% endfor %}
</div>
{% else %}
<p class="loading">
    Loading today's deals...<br>
    <small>Generating fresh AI descriptions – this only happens once per day.</small>
</p>
{% endif %}

{% if total_pages > 1 %}
<div class="pagination">
    {% for p in range(1, total_pages+1) %}
        {% if p == page %}
        <span style="background:{{button}};padding:10px 16px;border-radius:12px;font-weight:700">{{p}}</span>
        {% else %}
        <a href="{{ page_url(p) }}">{{p}}</a>
        {% endif %}
    {% endfor %}
</div>
{% endif %}

<footer>
    <p><strong>As an Amazon Associate, I earn from qualifying purchases.</strong></p>
    <p>FyboBuybo is an independent UK deals site. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates.</p>
</footer>

</body>
</html>
"""

# ---------------- ROUTES ---------------- #
def render_page(title, description, heading, subtitle, products, page=1, page_url=lambda p: "#"):
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    history = load_history()
    categories = get_categories(history)
    canonical = SITE_URL + request.path

    paged_products, total_items = paginate(products, page)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    return render_template_string(
        BASE_HTML,
        title=title,
        description=description,
        heading=heading,
        subtitle=subtitle,
        products=paged_products,
        categories=categories,
        css=css,
        canonical_url=canonical,
        slugify=slugify,
        total_pages=total_pages,
        page=page,
        page_url=page_url,
        button=theme["button"]
    )

@app.route("/")
def home():
    products = refresh_products(background=False)[:ITEMS_PER_PAGE]
    return render_page(
        title="FyboBuybo – Trending UK Deals & Popular Products",
        description="Discover today's trending UK deals and popular products across electronics, home, toys, beauty and more. Independently curated and refreshed daily.",
        heading="FyboBuybo – Trending UK Deals",
        subtitle="A curated look at popular products and online bestsellers, refreshed daily.",
        products=products
    )

@app.route("/category/<slug>")
def category(slug):
    history = load_history()
    # Deduplicate by name + url
    unique_products = {}
    for day in history.values():
        for p in day:
            if slugify(p["category"]) == slug:
                key = p["name"] + p["url"]
                unique_products[key] = p
    products = list(unique_products.values())
    
    if not products:
        abort(404)
    cat_name = products[0]["category"]

    def page_url(p):
        return url_for("category", slug=slug, page=p)

    page = int(request.args.get("page", 1))
    return render_page(
        title=f"{cat_name} Deals – FyboBuybo",
        description=f"Explore popular and trending {cat_name} products in the UK, featuring bestsellers and well-reviewed items.",
        heading=f"{cat_name} Deals",
        subtitle=f"Hand-picked popular products in {cat_name}, updated from our daily selections.",
        products=products,
        page=page,
        page_url=page_url
    )

@app.route("/all-deals")
def all_deals():
    history = load_history()
    today_str = str(datetime.date.today())
    today_products = refresh_products(background=True)
    
    # Deduplicate all products
    unique_products = {}
    for p in today_products:
        key = p["name"] + p["url"]
        unique_products[key] = p
    for date, day_prods in history.items():
        if date != today_str:
            for p in day_prods:
                key = p["name"] + p["url"]
                unique_products[key] = p
    
    all_products = list(unique_products.values())

    def page_url(p):
        return url_for("all_deals", page=p)

    page = int(request.args.get("page", 1))
    return render_page(
        title="All Deals – FyboBuybo",
        description="Browse all trending UK deals and popular products across categories in one place.",
        heading="All Deals",
        subtitle="Our full selection of today's trending products in the UK.",
        products=all_products,
        page=page,
        page_url=page_url
    )

# ---------------- SEO FILES ---------------- #
@app.route("/robots.txt")
def robots():
    txt = f"""
User-agent: *
Disallow:

Sitemap: {SITE_URL}/sitemap.xml
"""
    return Response(txt, mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    history = load_history()
    urls = [SITE_URL + "/"] + [SITE_URL + "/all-deals"]
    for day_products in history.values():
        for p in day_products:
            urls.append(SITE_URL + "/category/" + slugify(p["category"]))

    sitemap_xml = "<?xml version='1.0' encoding='UTF-8'?>\n"
    sitemap_xml += "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"
    for url in sorted(set(urls)):
        sitemap_xml += f"  <url>\n    <loc>{url}</loc>\n  </url>\n"
    sitemap_xml += "</urlset>"
    return Response(sitemap_xml, mimetype="application/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
