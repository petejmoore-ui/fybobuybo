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

# Real top rechargeable hand warmers – December 18, 2025 (Amazon UK Best Sellers)
PRODUCTS = [
    {"name": "COTOP Hand Warmers Rechargeable 2 Pack 6000mAh", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/81a2hQ1jK3L._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/COTOP-Rechargeable-Handwarmers-Electric-Portable/dp/B0C6G8J7P8?tag={AFFILIATE_TAG}"},
    {"name": "OCOOPA Magnetic Hand Warmers Rechargeable 2 Pack", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/71V8g8Zf0uL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/OCOOPA-Magnetic-Rechargeable-Handwarmers-Certified/dp/B0CH34CB3P?tag={AFFILIATE_TAG}"},
    {"name": "Wopigh Hand Warmers Rechargeable 2 Pack", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/71L5f5rE2L._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Wopigh-Magnetic-Rechargeable-Handwarmers-Portable/dp/B0DM1WK3YJ?tag={AFFILIATE_TAG}"},
    {"name": "Gaiatop Magnetic Hand Warmers Rechargeable 2 Pack", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/81kW5uO8eGL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Gaiatop-Magnetic-Rechargeable-Portable-Penguin/dp/B0CL5QJ2QW?tag={AFFILIATE_TAG}"},
    {"name": "OCOOPA Dual-Sided Hand Warmers Rechargeable", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/61d2z9rXJPL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/OCOOPA-Dual-Sided-Rechargeable-Handwarmers-Certified/dp/B0FHPF3WXM?tag={AFFILIATE_TAG}"},
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
