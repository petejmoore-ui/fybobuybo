import os
import json
import datetime
from flask import Flask, render_template_string
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "cache.json"

AFFILIATE_TAG = "whoaccepts-21"  # Your tag!

# Updated varied trending products – December 18, 2025 (Best Sellers/Movers & Shakers)
PRODUCTS = [
    {"name": "Hydrocolloid Pimple Patches Pack", "category": "Beauty", 
     "image": "https://m.media-amazon.com/images/I/71example-pimplepatches-large.jpg",
     "url": f"https://www.amazon.co.uk/Hydrocolloid-Pimple-Patches-Absorbing-Spots/dp/B0example-patches?tag={AFFILIATE_TAG}"},
    {"name": "Gua Sha Facial Tool Jade Stone", "category": "Beauty", 
     "image": "https://m.media-amazon.com/images/I/81example-guasha-large.jpg",
     "url": f"https://www.amazon.co.uk/Gua-Sha-Facial-Tool-Jade/dp/B0example-guasha?tag={AFFILIATE_TAG}"},
    {"name": "Stanley Quencher H2.0 Insulated Tumbler", "category": "Home & Kitchen", 
     "image": "https://m.media-amazon.com/images/I/71example-stanley-large.jpg",
     "url": f"https://www.amazon.co.uk/Stanley-Quencher-Insulated-Tumbler/dp/B0example-stanley?tag={AFFILIATE_TAG}"},
    {"name": "Levoit Air Purifier for Home", "category": "Home & Kitchen", 
     "image": "https://m.media-amazon.com/images/I/61wT8py+YNL._AC_SY879_.jpg",
     "url": f"https://www.amazon.co.uk/Levoit-Air-Purifier-Home-Allergies/dp/B07VVK39F7?tag={AFFILIATE_TAG}"},
    {"name": "Lululemon Athleisure Align Leggings", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/71example-lululemon-large.jpg",
     "url": f"https://www.amazon.co.uk/Lululemon-Align-High-Rise-Legging-28/dp/B0example-lulu?tag={AFFILIATE_TAG}"},
    {"name": "Matcha Green Tea Powder 100g", "category": "Grocery", 
     "image": "https://m.media-amazon.com/images/I/81example-matcha-large.jpg",
     "url": f"https://www.amazon.co.uk/Matcha-Green-Tea-Powder-Organic/dp/B0example-matcha?tag={AFFILIATE_TAG}"},
    {"name": "Mushroom Coffee Blend 250g", "category": "Grocery", 
     "image": "https://m.media-amazon.com/images/I/71example-mushroomcoffee-large.jpg",
     "url": f"https://www.amazon.co.uk/Mushroom-Coffee-Blend-Organic-Lions/dp/B0example-mushroom?tag={AFFILIATE_TAG}"},
    {"name": "Fake Plants for Home Decor Set", "category": "Home & Kitchen", 
     "image": "https://m.media-amazon.com/images/I/81example-fakeplants-large.jpg",
     "url": f"https://www.amazon.co.uk/Artificial-Plants-Home-Decor-Bathroom/dp/B0example-plants?tag={AFFILIATE_TAG}"},
    {"name": "Adjustable Phone Stand Desk Holder", "category": "Electronics", 
     "image": "https://m.media-amazon.com/images/I/71example-phonestand-large.jpg",
     "url": f"https://www.amazon.co.uk/Adjustable-Phone-Stand-Desk-Holder/dp/B0example-stand?tag={AFFILIATE_TAG}"},
]

CSS = """
<style>
body{margin:0;background:#0d0d1f;color:#fff;font-family:'Outfit',sans-serif;padding:20px}
h1{text-align:center;font-size:3.5rem;background:linear-gradient(90deg,#ff4e4e,#8b5cf6);-webkit-background-clip:text;color:transparent}
.subtitle{text-align:center;opacity:.8;margin-bottom:40px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;max-width:1400px;margin:auto}
.card{background:#161630;border-radius:22px;padding:22px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.6);transition:.3s}
.card:hover{transform:scale(1.05)}
img{width:100%;border-radius:16px}
.tag{background:#8b5cf6;padding:6px 14px;border-radius:20px;font-size:.85rem;display:inline-block;margin-bottom:10px}
button{background:#ff4e4e;border:none;padding:14px 36px;border-radius:50px;font-size:1.2rem;font-weight:900;color:white;cursor:pointer}
.hook{margin:14px 0;line-height:1.5}
footer{text-align:center;opacity:.6;margin:60px 0}
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
<h1>FyboBuybo</h1>
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
            messages=[{
                "role": "user",
                "content": f"Create a unique, exciting 1-2 sentence sales hook for this trending UK Amazon product: '{name}'. Make it urgent and fun, use **bold** for emphasis, vary the style, and end with a strong call to action like 'Snag it now!' or 'Don't wait!'"
            }],
            temperature=1.0,
            max_tokens=90
        )
        return r.choices[0].message.content
    except Exception:
        return f"**{name}** is the must-have everyone's rushing to buy!<br>**Grab yours before stocks run out!** 🔥"

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
