# app.py
import os
from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import boto3
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env
load_dotenv()

# Flask app
app = Flask(__name__)

# Amazon PAAPI credentials from environment
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_ASSOC_TAG = os.getenv("AWS_ASSOC_TAG")
AWS_REGION = os.getenv("AWS_REGION", "uk")  # default UK

# Initialize Amazon client
paapi = boto3.client(
    "advertising-api",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Global variable to store trending items
trending_items = []

# Function to fetch trending items from Amazon
def fetch_trending_items():
    global trending_items
    try:
        response = paapi.get_items(
            Marketplace="www.amazon.co.uk",
            ItemIds=[],
            Resources=[
                "ItemInfo.Title",
                "Images.Primary.Large",
                "Offers.Listings.Price"
            ]
        )
        trending_items = []
        for item in response.get("ItemsResult", {}).get("Items", []):
            trending_items.append({
                "title": item["ItemInfo"]["Title"]["DisplayValue"],
                "image": item["Images"]["Primary"]["Large"]["URL"],
                "price": item.get("Offers", {}).get("Listings", [{}])[0].get("Price", {}).get("DisplayAmount", ""),
                "url": f"https://www.amazon.co.uk/dp/{item['ASIN']}?tag={AWS_ASSOC_TAG}"
            })
        print(f"[{datetime.now()}] Trending items updated: {len(trending_items)} items")
    except Exception as e:
        print("Error fetching trending items:", e)

# Schedule fetching every 6 hours
scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_trending_items, trigger="interval", hours=6)
scheduler.start()

# Fetch initially
fetch_trending_items()

# Routes
@app.route("/")
def index():
    return render_template("index.html", items=trending_items)

# Run Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
