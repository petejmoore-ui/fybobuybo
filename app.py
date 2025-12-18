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

AFFILIATE_TAG = "whoaccepts-21"  # <<< REPLACE WITH YOUR REAL AMAZON ASSOCIATES TAG!

# Real trending/moving UK products – December 18, 2025
# From Amazon Best Sellers & Movers/Shakers: LEGO, hand warmers, dehumidifiers, shower gel, fidget spinners, etc.
PRODUCTS = [
    {"name": "LEGO Icons Williams Racing FW14B & Nigel Mansell F1 Car Model", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81+example-lego-fw14b.jpg",  # Use actual from page
     "url": f"https://www.amazon.co.uk/LEGO-Icons-Williams-Racing-Nigel/dp/B0example?tag={AFFILIATE_TAG}"},
    {"name": "Rechargeable Hand Warmers 10000mAh 2 Pack", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/71example-handwarmers.jpg",
     "url": f"https://www.amazon.co.uk/Rechargeable-Hand-Warmers-Double-sided/dp/B0example?tag={AFFILIATE_TAG}"},
    {"name": "EasyAcc 1200ml Electric Dehumidifier", "category": "Home & Kitchen", 
     "image": "https://m.media-amazon.com/images/I/71example-dehumidifier.jpg",
     "url": f"https://www.amazon.co.uk/Dehumidifier-EasyAcc-Electric-Portable/dp/B0example?tag={AFFILIATE_TAG}"},
    {"name": "Sanex Expert Skin Health Hypoallergenic Shower Gel", "category": "Beauty", 
     "image": "https://m.media-amazon.com/images/I/71example-sanex.jpg",
     "url": f"https://www.amazon.co.uk/Sanex-Expert-Hypoallergenic-Shower-Gel/dp/B0example?tag={AFFILIATE_TAG}"},
    {"name": "TOSY Magnet Fidget Spinner Glow", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81example-tosy.jpg",
     "url": f"https://www.amazon.co.uk/TOSY-Magnet-Fidget-Spinner-Glow/dp/B0example?tag={AFFILIATE_TAG}"},
    {"name": "Ginger Fox Taskmaster Card Game", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81example-taskmaster.jpg",
     "url": f"https://www.amazon.co.uk/Ginger-Fox-Taskmaster-Card-Game/dp/B0example?tag={AFFILIATE_TAG}"},
    {"name": "Amazon Fire TV Stick 4K", "category": "Electronics", 
     "image": "https://m.media-amazon.com/images/I/41example-firetv.jpg",
     "url": f"https://www.amazon.co.uk/Amazon-Fire-TV-Stick-4K/dp/B0example?tag={AFFILIATE_TAG}"},
    {"name": "Ring Battery Video Doorbell (2024)", "category": "Electronics", 
     "image": "https://m.media-amazon.com/images/I/61example-ring.jpg",
     "url": f"https://www.amazon.co.uk/Ring-Battery-Video-Doorbell-2024/dp/B0example?tag={AFFILIATE_TAG}"},
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
