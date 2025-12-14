import os
from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import requests
from groq import GroqClient
from amazon_paapi import AmazonAPI  # Use the official Amazon PAAPI SDK

# Load environment variables
load_dotenv()

AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
AMAZON_PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
REGION = "uk"

app = Flask(__name__)

# Fallback content
fallback_products = [
    {
        "title": "Sample Product 1",
        "image": "https://via.placeholder.com/300",
        "link": "#",
        "category": "Fallback",
        "description": "This is fallback content while live data is loading."
    },
    {
        "title": "Sample Product 2",
        "image": "https://via.placeholder.com/300",
        "link": "#",
        "category": "Fallback",
        "description": "This is fallback content while live data is loading."
    },
]

# In-memory store
trending_products = fallback_products.copy()

# Initialize Amazon API
amazon = AmazonAPI(AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG, REGION)

# Initialize Groq client
groq_client = GroqClient(api_key=GROQ_API_KEY)

def fetch_trending_products():
    global trending_products
    try:
        # Fetch top trending products via Amazon PAAPI
        items = amazon.get_top_selling_items(limit=8, category="All")
        products = []
        for item in items:
            products.append({
                "title": item.title,
                "image": item.image_url,
                "link": item.detail_page_url,
                "category": item.category,
                "description": item.features[0] if item.features else "Amazing product!"
            })
        trending_products = products
    except Exception as e:
        print("Error fetching products:", e)
        trending_products = fallback_products

# Schedule automatic updates every 6 hours
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_trending_products, "interval", hours=6)
scheduler.start()

@app.route("/")
def index():
    return render_template("index.html", products=trending_products)

if __name__ == "__main__":
    fetch_trending_products()  # Initial fetch
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
