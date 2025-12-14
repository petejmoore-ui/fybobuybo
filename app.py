import os, json, datetime
from flask import Flask, render_template
from groq import Groq
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

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

def refresh_hooks():
    today = str(datetime.date.today())
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            data = json.load(f)
            if data.get("date") == today:
                return data["products"]
    
    products = []
    for p in PRODUCTS:
        prompt = f"Write a short, exciting 2-line hype hook for this trending UK product: '{p['name']}'. Use bold and keep it honest."
        try:
            hook = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"user","content":prompt}],
                temperature=0.85,
                max_tokens=120
            ).choices[0].message.content.strip()
        except:
            hook = f"<b>{p['name']} is flying off shelves across the UK!</b><br>Perfect for right now."
        products.append({**p, "hook": hook})
    
    with open(CACHE_FILE, "w") as f:
        json.dump({"date": today, "products": products}, f)
    return products

@app.route("/")
def home():
    return render_template("index.html", products=refresh_hooks())

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_hooks, 'cron', hour=6)
    scheduler.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
