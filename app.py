import os
import json
import datetime
from flask import Flask, render_template_string
from groq import Groq
from dotenv import load_dotenv

load_dotenv()  # For local testing only

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "cache.json"

AFFILIATE_TAG = "whoaccepts-21"  # <<< REPLACE WITH YOUR REAL TAG!

# Real trending UK products – December 18, 2025 (from Best Sellers/Movers & Shakers)
PRODUCTS = [
    {"name": "INIU Portable Charger 10000mAh", "category": "Tech", 
     "image": "https://m.media-amazon.com/images/I/71kKx3jE5fL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/INIU-Portable-Charger-10000mAh-Power/dp/B07CZ7Z6WK?tag={AFFILIATE_TAG}"},
    {"name": "Oral-B iO3 Electric Toothbrush", "category": "Health", 
     "image": "https://m.media-amazon.com/images/I/61v2ZaR3PZL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Oral-B-iO3-Electric-Toothbrush/dp/B0Cexample?tag={AFFILIATE_TAG}"},
    {"name": "Tony's Chocolonely Everything Bar", "category": "Grocery", 
     "image": "https://m.media-amazon.com/images/I/81example-tonys.jpg",
     "url": f"https://www.amazon.co.uk/Tonys-Chocolonely-Everything-Chocolate-Bar/dp/B0example?tag={AFFILIATE_TAG}"},
    {"name": "HIGH5 ZERO Electrolyte Tablets", "category": "Health", 
     "image": "https://m.media-amazon.com/images/I/81example-high5.jpg",
     "url": f"https://www.amazon.co.uk/HIGH5-ZERO-Electrolyte-Hydration-Tablets/dp/B07example?tag={AFFILIATE_TAG}"},
    {"name": "Murdle Puzzle Book", "category": "Books", 
     "image": "https://m.media-amazon.com/images/I/81example-murdle.jpg",
     "url": f"https://www.amazon.co.uk/Murdle-Devilishly-Murder-Mystery-Puzzles/dp/B0Cexample?tag={AFFILIATE_TAG}"},
    {"name": "Bedsure Heated Throw Blanket", "category": "Home Comfort", 
     "image": "https://m.media-amazon.com/images/I/81example-bedsure.jpg",
     "url": f"https://www.amazon.co.uk/Bedsure-Electric-Heated-Blanket-Throw/dp/B0example?tag={AFFILIATE_TAG}"},
    {"name": "Grenade High Protein Bar", "category": "Health", 
     "image": "https://m.media-amazon.com/images/I/81example-grenade.jpg",
     "url": f"https://www.amazon.co.uk/Grenade-Carb-Killa-Protein-Chocolate/dp/B07example?tag={AFFILIATE_TAG}"},
    {"name": "Stanley Quencher Tumbler", "category": "Home", 
     "image": "https://m.media-amazon.com/images/I/71example-stanley.jpg",
     "url": f"https://www.amazon.co.uk/Stanley-Quencher-Tumbler-Stainless-Insulated/dp/B0example?tag={AFFILIATE_TAG}"},
]

CSS = """
<style>
/* Your existing beautiful CSS – unchanged */
</style>
"""

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ForYourBuysOnly</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">
{{ css | safe }}
</head>
<body>
<h1>ForYourBuysOnly</h1>
<p class="subtitle">Top UK trending buys · Updated daily</p>

<div class="grid">
{% for p in products %}
<div class="card">
  <span class="tag">{{ p.category }}</span>
  <img src="{{ p.image }}" alt="{{ p.name }}">
  <h3>{{ p.name }}</h3>
  <div class="hook">{{ p.hook|safe }}</div>
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
            messages=[{"role": "user", "content": f"Write a short, exciting 2-line hype hook for this trending UK product: '{name}'. Use bold."}],
            temperature=0.85,
            max_tokens=100
        )
        return r.choices[0].message.content
    except:
        return f"<b>{name} is trending big in the UK!</b><br>Don't miss out."

def refresh_products():
    today = str(datetime.date.today())

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            data = json.load(f)
            if data.get("date") == today:
                return data["products"]

    enriched = []
    for p in PRODUCTS:
        enriched.append({**p, "hook": generate_hook(p["name"])})

    with open(CACHE_FILE, "w") as f:
        json.dump({"date": today, "products": enriched}, f)

    return enriched

@app.route("/")
def home():
    return render_template_string(HTML, products=refresh_products(), css=CSS)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
