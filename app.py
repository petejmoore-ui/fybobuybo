import os
from flask import Flask, render_template
from dotenv import load_dotenv
import boto3
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from groq_client import GroqClient  # Correct import

load_dotenv()

app = Flask(__name__)

# --- Amazon PAAPI Setup ---
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG")
REGION = os.getenv("REGION", "uk")

amazon_client = boto3.client(
    "productadvertisingapi",
    aws_access_key_id=AMAZON_ACCESS_KEY,
    aws_secret_access_key=AMAZON_SECRET_KEY,
    region_name=REGION
)

# --- Groq Setup ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = GroqClient(api_key=GROQ_API_KEY)

# --- Trending Data ---
trending_items = []

def fetch_trending():
    global trending_items
    # Example: fetch 8 UK trending products (replace with real PAAPI call)
    trending_items = [
        {
            "category": "Drinks",
            "title": "Guinness Draught Nitrosurge",
            "description": "Game-changing beer for UK lovers",
            "image": "https://example.com/guinness.jpg",
            "url": "#"
        },
        # ... add more items
    ]

scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_trending, trigger="interval", hours=12)
scheduler.start()

# --- Routes ---
@app.route("/")
def home():
    return render_template("index.html", items=trending_items)

if __name__ == "__main__":
    fetch_trending()  # Initial load
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
