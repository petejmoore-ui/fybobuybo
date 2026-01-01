import os
import json
import re
import datetime
from threading import Thread
from products_data import PRODUCTS
from blog_data import BLOG_POSTS

from flask import Flask, render_template_string, request, url_for, abort, Response
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "/data/cache.json"
HISTORY_FILE = "/data/history.json"
AFFILIATE_TAG = "whoaccepts-21"
SITE_URL = "https://fybobuybo.com"
ITEMS_PER_PAGE = 12

# Ensure data directory exists
os.makedirs("/data", exist_ok=True)

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
        p_copy.setdefault("date_added", str(datetime.date.today()))
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
        return [{
            "name": p["name"],
            "category": p["category"],
            "image": p["image"],
            "url": p["url"],
            "info": p["info"],
            "hook": p["info"]
        } for p in PRODUCTS]
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
    today_str = str(datetime.date.today())
    today_products = history.get(today_str, []) or PRODUCTS
    cats = set()
    for p in today_products:
        cats.add(p["category"])
        if "season" in p:
            for s in p["season"].split(","):
                if s.strip():
                    cats.add(s.strip())
    return sorted(cats)

def paginate(items, page):
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return items[start:end], len(items)

def shorten_product_name(name, max_length=80):
    if len(name) <= max_length:
        return name
    for sep in [',', '(']:
        if sep in name:
            short = name.split(sep, 1)[0].strip()
            if len(short) <= max_length:
                return short
    words, out = name.split(), ""
    for w in words:
        if len(out + " " + w) <= max_length - 3:
            out += (" " if out else "") + w
        else:
            break
    return out + "..."

def ensure_hook(p):
    if "hook" not in p or p["hook"] == p.get("info"):
        p["hook"] = generate_hook(p["name"])
    return p

# ---------------- ROUTES ---------------- #
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


@app.route("/blog")
def blog_index():
    sorted_posts = sorted(
        BLOG_POSTS.items(),
        key=lambda x: x[1].get("date", "1900-01-01"),
        reverse=True
    )

    for slug, post in sorted_posts:
        date_obj = datetime.datetime.strptime(post["date"], "%Y-%m-%d")
        _ = date_obj.strftime("%B %d, %Y")

    return render_template_string("<h1>Blog OK</h1>")

# ---------------- SEO FILES ---------------- #
@app.route("/robots.txt")
def robots():
    return Response(f"Sitemap: {SITE_URL}/sitemap.xml", mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    return Response("<xml></xml>", mimetype="application/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
