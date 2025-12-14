from flask import Flask, render_template
import boto3
import os
from dotenv import load_dotenv

load_dotenv()  # Load API keys from .env

app = Flask(__name__)

# Amazon API setup
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_ASSOCIATE_TAG = os.getenv("AWS_ASSOCIATE_TAG")
REGION = os.getenv("REGION", "us-east-1")

client = boto3.client(
    "productadvertisingapi",  # This is pseudo-client; see note below
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION
)

def fetch_trending_products():
    """
    Fetch trending products using Amazon Product Advertising API
    """
    # Example placeholder: you can customize search or category
    response = client.search_items(
        Keywords="trending",
        SearchIndex="All",
        ItemCount=8,
        Resources=["Images.Primary.Large","ItemInfo.Title","Offers.Listings.Price","DetailPageURL"]
    )
    
    products = []
    for item in response['ItemsResult']['Items']:
        products.append({
            "title": item['ItemInfo']['Title']['DisplayValue'],
            "url": item['DetailPageURL'],
            "image": item['Images']['Primary']['Large']['URL'],
            "price": item['Offers']['Listings'][0]['Price']['DisplayAmount']
        })
    return products

@app.route("/")
def home():
    products = fetch_trending_products()
    return render_template("index.html", products=products)

if __name__ == "__main__":
    app.run(debug=True)
