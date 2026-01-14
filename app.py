# --- Full app.py with SEO improvements ---
import os, json, re, datetime, random
from threading import Thread
from products_data import PRODUCTS
from blog_data import BLOG_POSTS

from flask import Flask, render_template_string, request, url_for, abort, Response
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- Staging SEO safeguard ---
if os.environ.get("STAGING") == "true":
    @app.after_request
    def add_header(response):
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        return response

CACHE_FILE = "/data/cache.json"
HISTORY_FILE = "/data/history.json"
AFFILIATE_TAG = "whoaccepts-21"
SITE_URL = "https://www.fybobuybo.com"
ITEMS_PER_PAGE = 12
CACHE_REFRESH_DAYS = 10
PROMPT_VERSION = "v2.2-uk-seo-2026"

os.makedirs("data", exist_ok=True)
DATA_PATH = "data"

# ---------------- THEMES ---------------- #
THEMES = [{"bg":"#0f172a","card":"#1e293b","accent":"#38bdf8","button":"#0284c7","tag":"#7dd3fc","text_accent":"#bae6fd","gradient":"linear-gradient(90deg,#0284c7,#38bdf8)"}]

def get_daily_theme():
    return THEMES[datetime.date.today().timetuple().tm_yday % len(THEMES)]

# ---------------- AI HOOK GENERATION ---------------- #
HOOK_STYLES = ["benefit-first","lifestyle-story","quality-craft","quiet-genius"]
FALLBACK_HOOK = "A popular choice among UK shoppers for its quality and everyday appeal."

def generate_hook(product):
    if "hook_override" in product and product["hook_override"].strip():
        return product["hook_override"].strip()
    name = product["name"]
    category = product.get("category","")
    keywords = product.get("keywords",[])
    pain_points = product.get("pain_points",[])
    price_tier = product.get("price_tier","")
    style = random.choice(HOOK_STYLES)
    prompt = f"""
You are a sophisticated British copywriter creating calm, elegant 1–2 sentence product highlights 
loved by UK shoppers in 2026.

Core rules:
- Max 2 sentences
- Focus on practical benefits
- Avoid hype words
- Use <b> tags subtly around standout features
- Sound refined, trustworthy

Style: {style}
Category: {category}
Price feel: {price_tier}
Common UK context: {', '.join(pain_points) if pain_points else 'everyday practicality and lasting value'}
Target phrases: {', '.join(keywords) if keywords else 'none'}
Product: {name}
Output only the sentences.
"""
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.72 + random.uniform(-0.08, 0.08),
            max_tokens=90
        )
        hook = r.choices[0].message.content.strip()
        hook = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', hook)
        hook = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', hook)
        if not re.search(r'[.!?]$', hook):
            hook += " It’s quietly appreciated among UK shoppers."
        return hook
    except Exception as e:
        print(f"Groq error for '{name}': {e}")
        return FALLBACK_HOOK

# ---------------- CACHING ---------------- #
def should_refresh_cache():
    if not os.path.exists(CACHE_FILE):
        return True
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
        cache_date = datetime.datetime.fromisoformat(cache.get("date","2000-01-01T00:00:00"))
        days_old = (datetime.datetime.now() - cache_date).days
        if days_old >= CACHE_REFRESH_DAYS:
            return True
        if cache.get("prompt_version") != PROMPT_VERSION:
            return True
        return False
    except:
        return True

def load_or_generate_hooks(products):
    enriched = []
    for p in products:
        p_copy = dict(p)
        p_copy["hook"] = generate_hook(p)
        p_copy.setdefault("date_added", str(datetime.date.today()))
        p_copy["hook_version"] = PROMPT_VERSION
        enriched.append(p_copy)
    today_iso = datetime.datetime.now().isoformat()
    with open(CACHE_FILE,"w",encoding="utf-8") as f:
        json.dump({"date": today_iso,"prompt_version":PROMPT_VERSION,"products":enriched},f,indent=2,ensure_ascii=False)
    history = load_history()
    history_key = datetime.date.today().isoformat()
    history[history_key] = enriched
    save_history(history)
    return enriched

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(data):
    with open(HISTORY_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)

def refresh_products(background=False):
    today = str(datetime.date.today())
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache = json.load(f)
            cache_date_str = cache.get("date","")
            if cache_date_str.startswith(today):
                return cache.get("products",[])
            cache_date = datetime.datetime.fromisoformat(cache_date_str)
            if (datetime.datetime.now()-cache_date).days < CACHE_REFRESH_DAYS and cache.get("prompt_version")==PROMPT_VERSION:
                return cache.get("products",[])
        except Exception as e:
            print(f"Cache read failed: {e}")
    enriched = load_or_generate_hooks(PRODUCTS)
    return enriched

# ---------------- HELPERS ---------------- #
def slugify(text):
    text = text.lower()
    text = re.sub(r'&', '-and-', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    return text

def normalize_for_match(text):
    if not text:
        return ""
    return text.lower().replace("'", "").replace(" ", "").replace("-", "")

def get_nav_items():
    products = PRODUCTS
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache = json.load(f)
            products = cache.get("products", PRODUCTS)
        except:
            pass
    categories = sorted({p["category"] for p in products if p.get("category")})
    seasons_set = set()
    for p in products:
        if p.get("season"):
            for s in p["season"].split(","):
                clean = s.strip()
                if clean:
                    seasons_set.add(clean)
    important_seasons_order = [
        "Valentine's Day","Mother's Day","Easter","Father's Day",
        "Summer Gifts","Back to School","Halloween","Christmas"
    ]
    important_seasons = [s for s in important_seasons_order if s in seasons_set]
    other_seasons = sorted(seasons_set - set(important_seasons))
    seasons = other_seasons + important_seasons
    return {"categories": categories,"seasons": seasons}

def paginate(items, page):
    start = (page-1)*ITEMS_PER_PAGE
    end = start+ITEMS_PER_PAGE
    return items[start:end], len(items)

def shorten_product_name(name,max_length=80):
    if len(name)<=max_length:
        return name
    for sep in [',','(']:
        if sep in name:
            short = name.split(sep,1)[0].strip()
            if len(short)<=max_length:
                return short
    words,out = name.split(), ""
    for w in words:
        if len(out + " " + w) <= max_length-3:
            out += (" " if out else "") + w
        else:
            break
    return out+"..."

def ensure_hook(p):
    if "hook" not in p or not p["hook"]:
        p["hook"] = FALLBACK_HOOK
    return p

# ---------------- CSS ---------------- #
CSS_TEMPLATE = """<style>
body { margin:0; background:{{bg}}; color:#fff; font-family:'Outfit',sans-serif; padding:20px 20px 40px; }
h1 { text-align:center; font-size:3rem; background:{{gradient}}; -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:40px 0 10px; }
.subtitle { text-align:center; opacity:.85; max-width:900px; margin:20px auto; color:{{text_accent}}; font-size:1.1rem; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:24px; max-width:1400px; margin:auto; }
.card { background:{{card}}; border-radius:22px; padding:20px; text-align:center; box-shadow:0 20px 40px rgba(0,0,0,.6); transition:transform .3s,box-shadow .3s; }
.card:hover { transform:translateY(-8px); box-shadow:0 30px 60px rgba(0,0,0,.7); }
img { width:100%; border-radius:16px; margin:16px 0; }
.tag { background:{{tag}}; padding:6px 14px; border-radius:20px; font-size:.85rem; display:inline-block; margin-bottom:12px; }
button {
    background:{{button}}; border:none; padding:16px 36px; border-radius:50px; font-size:1.1rem; font-weight:900;
    color:white; cursor:pointer; transition:.3s; animation: pulse 2.5s infinite ease-in-out;
}
button:hover { opacity:.9; transform:scale(1.05); animation:none; }
@keyframes pulse { 0%{box-shadow:0 0 0 0 rgba(2,132,199,0.4);} 70%{box-shadow:0 0 0 12px rgba(2,132,199,0);} 100%{box-shadow:0 0 0 0 rgba(2,132,199,0);} }
@media (prefers-reduced-motion: reduce) { button{animation:none;} }
footer { text-align:center; opacity:.7; margin:80px 0 40px; font-size:.9rem; line-height:1.6; }
a { color:{{text_accent}}; text-decoration:none; }
nav { background:{{card}}; padding:16px; margin:20px 0 40px; border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,.4); text-align:center; position:relative; }
nav a { margin:0 16px; color:{{text_accent}}; font-weight:700; font-size:1.1rem; transition:.2s; }
nav a:hover { opacity:.8; }
nav .season-link { color: #f472b6; }
nav .season-link:hover { opacity: 0.9; color: #fda4af; }
.seasons-dropdown { display: none; position: relative; margin: 0 8px; }
.seasons-dropdown button { background: #334155; color: #bae6fd; border: 1px solid #475569; padding: 8px 16px; border-radius: 12px; font-weight: 600; font-size: 1rem; cursor: pointer; transition: all 0.2s; }
.seasons-dropdown button:hover { background: #475569; color: white; }
.dropdown-content { display: none; position: absolute; top: 100%; left: 50%; transform: translateX(-50%); background: {{card}}; border-radius: 12px; padding: 12px 0; min-width: 180px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); z-index: 100; margin-top: 8px; }
.dropdown-content a { display: block; padding: 10px 20px; color: {{text_accent}}; text-decoration: none; font-size: 1rem; white-space: nowrap; }
.dropdown-content a:hover { background: #334155; }
.pagination { display:flex; justify-content:center; gap:16px; margin:40px 0; }
.pagination a { background:{{button}}; padding:10px 16px; border-radius:12px; color:white; text-decoration:none; font-weight:700; transition:.2s; }
.pagination a:hover { opacity:.9; }
.loading { text-align:center; opacity:.8; margin:80px 0; font-size:1.3rem; color:{{text_accent}}; }
.grid:has(> .card:only-child) .card { max-width: 600px; margin: 0 auto; }
.grid:has(> .card:only-child) img { max-width: 500px; width: 100%; height: auto; margin: 20px auto; display: block; border-radius: 16px; }
.card h2 { min-height: 70px; display: flex; align-items: center; justify-content: center; margin: 12px 0; font-size: 1.25rem; line-height: 1.3; font-weight: 900; }
.card img { width: 100%; max-height: 380px; object-fit: contain; background: #111827; border-radius: 16px; margin: 16px 0; }
.card > a[onclick] { margin: 20px 0 10px; }
.card p:last-of-type { margin: 10px 0; font-size: .85rem; opacity: .7; }
@media (max-width:768px) { nav a { margin:0 10px; font-size:1rem; } .grid { grid-template-columns:1fr; } nav a.season-link { display: none; } .seasons-dropdown { display: inline-block; } }
@media (min-width:769px) { .seasons-dropdown { display: none !important; } }
</style>"""

# ---------------- BASE HTML ---------------- #
BASE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title>
<meta name="description" content="{{ description }}">
<link rel="canonical" href="{{ canonical_url }}">
{% if next_page_url %}<link rel="next" href="{{ next_page_url }}">{% endif %}
{% if prev_page_url %}<link rel="prev" href="{{ prev_page_url }}">{% endif %}
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
    <a href="/blog">Blog</a>
    {% for cat in nav_items.categories %}
        <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
    {% endfor %}
    {% if nav_items.seasons %}
        <span style="margin:0 14px;opacity:0.5;">•</span>
        {% for season in nav_items.seasons %}
            <a href="/season/{{ slugify(season) }}" class="season-link">{{ season }}</a>
        {% endfor %}
        <div class="seasons-dropdown">
            <button>Seasons ▼</button>
            <div class="dropdown-content">
                {% for season in nav_items.seasons %}
                    <a href="/season/{{ slugify(season) }}">{{ season }}</a>
                {% endfor %}
            </div>
        </div>
    {% endif %}
</nav>
<script>
document.addEventListener("DOMContentLoaded", function() {
    const dropdowns = document.querySelectorAll(".seasons-dropdown");
    dropdowns.forEach(dropdown => {
        const btn = dropdown.querySelector("button");
        const content = dropdown.querySelector(".dropdown-content");
        if (!btn || !content) return;
        btn.addEventListener("click", function(e) {
            e.stopPropagation();
            const isOpen = content.style.display === "block";
            document.querySelectorAll(".dropdown-content").forEach(el => el.style.display = "none");
            content.style.display = isOpen ? "none" : "block";
        });
    });
    document.addEventListener("click", function(e) {
        if (!e.target.closest(".seasons-dropdown")) {
            document.querySelectorAll(".dropdown-content").forEach(el => el.style.display = "none");
        }
    });
});
</script>
<h1>{{ heading }}</h1>
<p class="subtitle">{{ subtitle }}</p>
{% if products %}
<div class="grid">
{% for p in products %}
<div class="card">
    <span class="tag">{{ p.category }}</span>
    <a href="/product/{{ slugify(p.name) }}">
        <h2>{{ shorten_product_name(p.name) }}</h2>
    </a>
    <a href="/product/{{ slugify(p.name) }}">
        <img src="{{ p.image }}" alt="{{ p.name }} – {{ p.info }}" loading="lazy">
    </a>
    <p>{{ p.hook|safe }}</p>
    {% if p.date_added %}
    <p style="font-size:0.85rem;opacity:.7;margin:16px 0 8px;color:#94a3b8;text-align:center;">
        ↳ Featured on {{ p.date_added }}
    </p>
    {% endif %}
    <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored">
        <button>View on Amazon</button>
    </a>
</div>
{% endfor %}
</div>
{% else %}
<p class="loading">Loading today's gifts...</p>
{% endif %}
<footer>
    <p><strong>As an Amazon Associate, I earn from qualifying purchases.</strong></p>
    <p>FyboBuybo is an independent UK gifts site. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates.</p>
</footer>
</body>
</html>
"""

# ---------------- PAGE RENDER ---------------- #
def render_page(title, description, heading, subtitle, products, page=1, page_url=lambda p:"#", related_products=None):
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    nav_items = get_nav_items()
    canonical = SITE_URL + request.path
    page_num = int(request.args.get("page", 1))
    if page_num > 1:
        canonical += f"?page={page_num}"
    paged_products, total_items = paginate(products, page)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    next_page_url = page_url(page + 1) if page < total_pages else None
    prev_page_url = page_url(page - 1) if page > 1 else None
    return render_template_string(
        BASE_HTML,
        title=title,
        description=description,
        heading=heading,
        subtitle=subtitle,
        products=paged_products,
        nav_items=nav_items,
        css=css,
        canonical_url=canonical,
        SITE_URL=SITE_URL,
        slugify=slugify,
        shorten_product_name=shorten_product_name,
        related_products=related_products or [],
        next_page_url=next_page_url,
        prev_page_url=prev_page_url
    )

# ---------------- ROUTES ---------------- #
@app.route("/")
def home():
    products = refresh_products(background=True)
    return render_page(
        title="FyboBuybo – Trending UK Gifts & Popular Presents",
        description="Discover today's trending UK gifts across toys, beauty, electronics, and more.",
        heading="FyboBuybo – Trending UK Gifts",
        subtitle="A curated selection of popular gifts and presents, refreshed daily.",
        products=products[:ITEMS_PER_PAGE]
    )

@app.route("/robots.txt")
def robots():
    return Response(f"User-agent: *\nDisallow:\nSitemap: {SITE_URL}/sitemap.xml", mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    history = load_history()
    urls = set()
    urls.add((SITE_URL + "/", str(datetime.date.today())))
    for day_products in history.values():
        for p in day_products:
            if p.get("category"):
                urls.add((f"{SITE_URL}/category/{slugify(p['category'])}", p.get("date_added", str(datetime.date.today()))))
            if p.get("name"):
                urls.add((f"{SITE_URL}/product/{slugify(p['name'])}", p.get("date_added", str(datetime.date.today()))))
    for season in ["Valentine's Day","Mother's Day","Easter","Father's Day","Summer Gifts","Back to School","Halloween","Christmas"]:
        urls.add((f"{SITE_URL}/season/{slugify(season)}", str(datetime.date.today())))
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, lastmod in sorted(urls):
        sitemap_xml += f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>\n"
    sitemap_xml += "</urlset>"
    return Response(sitemap_xml, mimetype="application/xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
