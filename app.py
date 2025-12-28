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
    "name": "From Ibiza to the Norfolk Broads: A Bowie Odyssey by James Briggs",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/61Kdkp7DPuL._SY466_.jpg",
    "url": f"https://www.amazon.co.uk/Ibiza-Norfolk-Broads-Bowie-Odyssey/dp/1837733112?tag={AFFILIATE_TAG}",
    "info": "Hilarious and heartfelt memoir of a lifelong Bowie fan cycling the iconic Life on Mars? lyric from Ibiza to the Norfolk Broads — blending travel adventure, music history, and mid-life reflection. Trending for its witty take on embracing the strange and living fearlessly like the Starman."
},
    
    {
    "name": "Always Remember by Charlie Mackesy",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/818fhGP49iL._SY385_.jpg",
    "url": f"https://www.amazon.co.uk/Always-Remember-Charlie-Mackesy/dp/152993197X?tag={AFFILIATE_TAG}",
    "info": "Heartwarming illustrated book of wisdom and comfort from the creator of The Boy, the Mole, the Fox and the Horse — a Christmas No.1 bestseller perfect for thoughtful gifting and quiet reflection."
},

{
    "name": "Guinness World Records 2026",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/8186fr4T+gL._SY425_.jpg",
    "url": f"https://www.amazon.co.uk/Guinness-World-Records-2026/dp/1913484569?tag={AFFILIATE_TAG}",
    "info": "The iconic annual edition packed with thousands of amazing new records, facts, and photos — a perennial favourite gift for curious minds of all ages."
},
{
    "name": "The 1% Club Official Quiz Book",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/81I3J2AZbRL._SY425_.jpg",
    "url": f"https://www.amazon.co.uk/1-Club-Official-Quiz-Book/dp/1529941126?tag={AFFILIATE_TAG}",
    "info": "Official companion to the hit ITV quiz show hosted by Lee Mack — packed with challenging logic puzzles and questions to test the sharpest minds at home."
},
{
    "name": "Diary of a Wimpy Kid: Partypooper by Jeff Kinney",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/91NDZEkcE7L._SY466_.jpg",
    "url": f"https://www.amazon.co.uk/Diary-Wimpy-Kid-Partypooper-Book/dp/0241663008?tag={AFFILIATE_TAG}",
    "info": "The latest hilarious instalment in the bestselling Diary of a Wimpy Kid series — perfect laugh-out-loud reading for kids and reluctant readers."
},
{
    "name": "Exit Strategy by Lee Child & Andrew Child (Jack Reacher)",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/81BL0gt7LcL._SY466_.jpg",
    "url": f"https://www.amazon.co.uk/Exit-Strategy-Jack-Reacher-Child/dp/0857505474?tag={AFFILIATE_TAG}",
    "info": "Another gripping thriller in the iconic Jack Reacher series — high-stakes action and sharp plotting for fans of fast-paced crime fiction."
},
{
    "name": "The Secret of Secrets by Dan Brown",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/81dHhoARp9L._SY466_.jpg",
    "url": f"https://www.amazon.co.uk/Secret-Secrets-Dan-Brown/dp/1529900548?tag={AFFILIATE_TAG}",
    "info": "The highly anticipated new mystery thriller from the master of conspiracies — packed with codes, symbols, and globe-trotting intrigue."
},
{
    "name": "The Long Shoe by Bob Mortimer",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/61Y8egjgeyL._SY466_.jpg",
    "url": f"https://www.amazon.co.uk/Long-Shoe-Bob-Mortimer/dp/1399613317?tag={AFFILIATE_TAG}",
    "info": "Hilarious and heartfelt memoir from the beloved comedian Bob Mortimer — full of absurd stories, warmth, and laugh-out-loud moments."
},
{
    "name": "Sunrise on the Reaping by Suzanne Collins (Hunger Games)",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/71mC7kMhg6L._SY466_.jpg",
    "url": f"https://www.amazon.co.uk/Sunrise-Reaping-Hunger-Games/dp/070234587X?tag={AFFILIATE_TAG}",
    "info": "The gripping new prequel to The Hunger Games series — returning to the world of Panem with high-stakes drama and unforgettable characters."
},
{
    "name": "Onyx Storm by Rebecca Yarros (Empyrean Series)",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/81dY-4XtCXL._SY466_.jpg",
    "url": f"https://www.amazon.co.uk/Onyx-Storm-Empyrean-Rebecca-Yarros/dp/0349443053?tag={AFFILIATE_TAG}",
    "info": "The highly anticipated third book in the addictive romantasy Empyrean series — dragons, romance, and epic battles for fans of Fourth Wing and Iron Flame."
},
{
        "name": "Oral-B Vitality Pro Electric Toothbrush For Adults, Christmas Gifts For Him/Her, 3 Brushing Modes Including Sensitive Plus, Gentle Cleaning, 2 Min Timer, 1 Toothbrush Head, Black",
        "category": "Beauty",
        "image": "https://m.media-amazon.com/images/I/51LbAMaBpnL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Oral-B-Vitality-Toothbrush-Including-Sensitive/dp/B0B18V92KS?tag={AFFILIATE_TAG}",
        "info": "Affordable electric toothbrush with 3 brushing modes including Sensitive Plus for gentle cleaning, 2-minute timer, and superior plaque removal vs manual brushing. Bestselling entry-level Oral-B model for everyday oral care and healthier gums."
    },
    {
        "name": "The Impossible Fortune by Richard Osman (Thursday Murder Club 5)",
        "category": "Books",
        "image": "https://m.media-amazon.com/images/I/71eTwnmHa3L._SY466_.jpg",
        "url": f"https://www.amazon.co.uk/Impossible-Fortune-multi-million-bestselling-Thursday/dp/0241743982?tag={AFFILIATE_TAG}",
        "info": "The latest cosy crime bestseller in the multi-million selling Thursday Murder Club series — perfect for fans of clever, heartwarming murder mysteries."
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
Write a calm, elegant 1–2 sentence description explaining why this product is popular among UK shoppers.
Focus on its practical benefits, quality, or appeal in daily life.
Vary the phrasing across different products — avoid repeating common words like "staple", "essential", or "go-to".
Use <b> tags subtly for key features.
End with a complete sentence.
Product: {name}
"""
            }],
            temperature=0.7,
            max_tokens=120
        )
        hook = r.choices[0].message.content.strip()
        hook = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', hook)
        if not re.search(r'[.!?]$', hook):
            hook += " among UK shoppers."
        return hook
    except Exception as e:
        print(f"Groq error: {e}")
        return "A popular choice among UK shoppers for its quality and everyday appeal."

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

def shorten_product_name(name, max_length=80):
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

def ensure_hook(p):
    # If hook is missing or fallback, regenerate
    if "hook" not in p or p["hook"] == p.get("info") or "well-regarded product" in p["hook"]:
        p["hook"] = generate_hook(p["name"])
    return p

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
    <a href="/all-gifts">All Gifts</a>
    {% for cat in categories %}
    <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
    {% endfor %}
</nav>

<h1>{{ heading }}</h1>
<p class="subtitle">{{ subtitle }}</p>

<p style="text-align:center;opacity:.7;margin-bottom:40px;">
✔ UK-focused · ✔ Updated daily · ✔ Thoughtfully curated gifts
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
        More <a href="/category/{{ slugify(p.category) }}">{{ p.category }}</a> gifts
    </p>
</div>
{% endfor %}
</div>
{% else %}
<p class="loading">
    Loading today's gifts...<br>
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
    <p>FyboBuybo is an independent UK gifts site. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates.</p>
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
        shorten_product_name=shorten_product_name,
        total_pages=total_pages,
        page=page,
        page_url=page_url,
        button=theme["button"]
    )

@app.route("/")
def home():
    products = refresh_products(background=False)[:ITEMS_PER_PAGE]
    return render_page(
        title="FyboBuybo – Trending UK Gifts & Popular Presents",
        description="Discover today's trending UK gifts and popular presents across toys, beauty, electronics and more. Independently curated and refreshed daily.",
        heading="FyboBuybo – Trending UK Gifts",
        subtitle="A curated selection of popular gifts and presents, refreshed daily.",
        products=products
    )

@app.route("/category/<slug>")
def category(slug):
    history = load_history()
    unique_products = {}
    for day in history.values():
        for p in day:
            if slugify(p["category"]) == slug:
                key = p["name"] + p["url"]
                unique_products[key] = p
    products = [ensure_hook(p) for p in unique_products.values()]
    
    if not products:
        abort(404)
    cat_name = products[0]["category"]

    def page_url(p):
        return url_for("category", slug=slug, page=p)

    page = int(request.args.get("page", 1))
    return render_page(
        title=f"{cat_name} Gifts – FyboBuybo",
        description=f"Explore popular and trending {cat_name} gifts in the UK, featuring thoughtful presents and bestsellers.",
        heading=f"{cat_name} Gifts",
        subtitle=f"Hand-picked popular gifts in {cat_name}, updated from our daily selections.",
        products=products,
        page=page,
        page_url=page_url
    )

@app.route("/all-gifts")
def all_gifts():
    history = load_history()
    today_str = str(datetime.date.today())
    today_products = refresh_products(background=True)
    
    unique_products = {}
    for p in today_products:
        key = p["name"] + p["url"]
        unique_products[key] = p
    for date, day_prods in history.items():
        if date != today_str:
            for p in day_prods:
                key = p["name"] + p["url"]
                unique_products[key] = p
    
    all_products = [ensure_hook(p) for p in unique_products.values()]

    def page_url(p):
        return url_for("all_gifts", page=p)

    page = int(request.args.get("page", 1))
    return render_page(
        title="All Gifts – FyboBuybo",
        description="Browse our complete collection of trending UK gifts and popular presents across all categories.",
        heading="All Gifts",
        subtitle="Every hand-picked popular gift from our daily selections.",
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
    urls = [SITE_URL + "/"] + [SITE_URL + "/all-gifts"]
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
