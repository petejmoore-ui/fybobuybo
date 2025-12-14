import os
from flask import Flask, render_template
from dotenv import load_dotenv
import boto3

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Amazon PAAPI client setup
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_ASSOCIATE_TAG = os.getenv("AWS_ASSOCIATE_TAG")
REGION = os.getenv("REGION", "uk")

client = boto3.client(
    "advertising",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

def get_trending_products():
    """Fetch trending products from Amazon (example: top-selling)."""
    # Replace this with actual PAAPI calls
    return [
        {
            "title": "Guinness Draught Nitrosurge",
            "description": "Game-changing beer with nitro technology!",
            "image_url": "https://via.placeholder.com/300",
            "url": "https://www.amazon.co.uk/dp/EXAMPLE?tag=" + AWS_ASSOCIATE_TAG
        },
        {
            "title": "Velvet Toilet Tissue 24 Rolls",
            "description": "Softest wipe ever, ultimate comfort.",
            "image_url": "https://via.placeholder.com/300",
            "url": "https://www.amazon.co.uk/dp/EXAMPLE2?tag=" + AWS_ASSOCIATE_TAG
        }
    ]

@app.route("/")
def home():
    products = get_trending_products()
    return render_template("index.html", products=products)

if __name__ == "__main__":
    app.run(debug=True)
