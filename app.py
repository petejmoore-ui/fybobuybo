import os, json, datetime
from flask import Flask, render_template_string
from groq import Groq
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "cache.json"

PRODUCTS = [
    {"name": "Guinness Draught Nitrosurge", "category": "Drinks"},
    {"name": "Velvet Toilet Tissue 24 Rolls", "category": "Household"},
    {"name": "Nutrition Geeks Magnesium Glycinate", "category": "Health"},
    {"name": "Herd Mentality Board Game", "category": "Games"},
    {"name": "Electric Heated Blanket", "category": "Home Comfort"},
    {"name": "Diary of a Wimpy Kid: Partypooper", "category": "Books"},
    {"name": "Murdle Puzzle Book", "category": "Books"},
    {"name": "INIU Portable Charger", "category": "Tech"},
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
  <img src="https://via.placeholder.com/400x400/111/fff?text={{ p.name.replace(' ','+') }}">
  <h3>{{ p.name }}</h3>
  <div class="hook">{{ p.hook|safe }}</div>
  <a href="https://www.amazon.co.uk/s?k={{ p.name.replace(' ','+') }}" target="_blank">
    <button>Get It Now 🔥</button>
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
                "content": f"Write a short, exciting 2-line hype hook for this trending UK product: '{name}'. Use bold."
            }],
            temperature=0.85,
            max_tokens=100
        )
        return r.choices[0].message.content
    except:
        return f"<b>{name} is trending across the UK.</b><br>Limited availability right now."

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
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_products, "cron", hour=6)
    scheduler.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
