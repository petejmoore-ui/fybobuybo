import os, json, datetime
from flask import Flask, render_template_string
from apscheduler.schedulers.background import BackgroundScheduler

try:
    from groq import Groq
except ImportError:
    Groq = None  # Handle missing Groq gracefully

app = Flask(__name__)

# Initialize Groq client only if API key exists
API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY) if API_KEY and Groq else None

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

CSS = """<style>
body { margin:0; background:#0d0d1f; color:#fff; font-family:'Outfit',sans-serif; padding:20px 10px; }
h1 { font-size:3.8rem; text-align:center; background:linear-gradient(90deg,#ff4e4e,#8b5cf6); -webkit-background-clip:text; color:transparent; }
.subtitle { text-align:center; opacity:0.8; font-size:1.4rem; margin-bottom:40px; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:28px; max-width:1400px; margin:0 auto; }
.card { background:#161630; border-radius:22px; padding:24px; text-align:center; transition:.3s; box-shadow:0 15px 40px rgba(0,0,0,.7); }
.card:hover { transform:scale(1.05); }
img { width:100%; border-radius:16px; margin-bottom:16px; }
.tag { display:inline-block; background:#8b5cf6; padding:6px 16px; border-radius:20px; font-size:0.9rem; margin-bottom:12px; }
button { background:#ff4e4e; border:none; padding:15px 40px; border-radius:50px; font-size:1.3rem; font-weight:900; cursor:pointer; }
.hook { margin:16px 0; line-height:1.5; font-size:1.1rem; }
footer { text-align:center; opacity:0.6; margin:80px 0 20px; }
.privacy { position:fixed; bottom:0; left:0; width:100%; background:#222; padding:10px; text-align:center; font-size:0.9rem; }
</style>"""

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"><title>ForYourBuysOnly UK</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">
{{ css }}
</head>
<body>
<h1>ForYourBuysOnly</h1>
<p class="subtitle">Top UK trending buys · Updated daily</p>
<div class="grid">
{% for p in products %}
<div class="card">
  <span class="tag">{{ p.category }}</span>
  <img src="https://via.placeholder.com/400x400/111/fff?text={{ p.name.replace(' ','+') }}">
  <h3>{{ p.name }}</h3>
  <div class="hook">{{ p.hook | safe }}</div>
  <a href="https://www.amazon.co.uk/s?k={{ p.name.replace(' ','+') }}" target="_blank"><button>Grab It Now 🔥</button></a>
</div>
{% endfor %}
</div>
<footer>Affiliate links may earn commission · Made with AI</footer>
<div class="privacy">No tracking · No cookies · Just top UK finds</div>
</body>
</html>
"""

def refresh_hooks():
    today = str(datetime.date.today())

    # Try reading cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                data = json.load(f)
                if data.get("date") == today:
                    return data["products"]
        except json.JSONDecodeError:
            pass

    products = []
    for p in PRODUCTS:
        hook = f"<b>{p['name']} is flying off shelves across the UK!</b><br>Perfect for right now."
        if client:
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role":"user","content":f"Write a short, exciting 2-line hype hook for '{p['name']}'."}],
                    temperature=0.85,
                    max_tokens=120
                )
                hook = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Groq API failed for {p['name']}: {e}")
        products.append({**p, "hook": hook})

    with open(CACHE_FILE, "w") as f:
        json.dump({"date": today, "products": products}, f)

    return products

@app.route("/")
def home():
    return render_template_string(HTML, products=refresh_hooks(), css=CSS)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_hooks, 'cron', hour=6)
    scheduler.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
