import os
import json
import datetime
import re
from flask import Flask, render_template_string, abort, Response, request, url_for
from groq import Groq
from dotenv import load_dotenv
from threading import Thread

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "/data/cache.json"
HISTORY_FILE = "/data/history.json"
AFFILIATE_TAG = "whoaccepts-21"
SITE_URL = "https://fybobuybo.com"
ITEMS_PER_PAGE = 12

# ---------------- PRODUCTS ---------------- #
PRODUCTS = [

   
{
    "name": "HAISSKY Lightweight Running Belt Waist Pack",
    "category": "Sports & Outdoors",
    "subcategory": "Running Essentials",
    "image": "https://m.media-amazon.com/images/I/51XulFnEUWL._AC_SX425_.jpg",
    "url": "https://amzn.to/3LpASn2?tag=whoaccepts-21",
    "info": "Slim, bounce-free running belt designed to carry phones, keys, and energy gels securely. Adjustable fit makes it ideal for everyday training and long runs."
},
{
    "name": "Reflective Running Armbands (Set of 4)",
    "category": "Sports & Outdoors",
    "subcategory": "Running Essentials",
    "season": "New Year Essentials",
    "image": "https://m.media-amazon.com/images/I/51IeDoQq7rL._AC_SX679_.jpg",
    "url": "https://amzn.to/3L9rfZK?tag=whoaccepts-21",
    "info": "High-visibility reflective armbands to improve safety during early morning and evening runs. Lightweight, adjustable, and suitable for all runners."
},
{
    "name": "LUMEFIT Running Vest Phone Holder - Hydration Vest with Water Bottle- Reflective Vest for Men and Women",
    "category": "Sports & Outdoors",
    "subcategory": "Running Essentials",
    "image": "https://m.media-amazon.com/images/I/8186wRKgTML._AC_SX679_.jpg",
    "url": "https://amzn.to/4sAitou?tag=whoaccepts-21",
    "info": "Breathable hydration vest with adjustable straps and front water bottles. Ideal for long runs, trail training, and increasing mileage."
},
{
    "name": "Touchscreen-Compatible Running Gloves",
    "category": "Sports & Outdoors",
    "subcategory": "Running Essentials",
    "season": "New Year Essentials",
    "image": "https://m.media-amazon.com/images/I/71DXUZ1PXuL._AC_SX679_.jpg",
    "url": "https://amzn.to/49iIrnF?tag=whoaccepts-21",
    "info": "Lightweight thermal running gloves with touchscreen fingertips. Keeps hands warm while allowing phone use during cold runs."
},
{
    "name": "Compression Running Tights for Training",
    "category": "Sports & Outdoors",
    "subcategory": "Running Essentials",
    "image": "https://m.media-amazon.com/images/I/51EJj5Gm67L._AC_SX679_.jpg",
    "url": "https://amzn.to/4aFtmia?tag=whoaccepts-21",
    "info": "Supportive compression tights designed to reduce muscle fatigue and improve comfort during long or recovery runs."
},
{
    "name": "Ear Warmers Headband with Ponytail Hole",
    "category": "Sports & Outdoors",
    "subcategory": "Running Essentials",
    "season": "Summer Essentials",
    "image": "https://m.media-amazon.com/images/I/713-9cSHBJL._AC_SX679_.jpg",
    "url": "https://amzn.to/49aRqZj?tag=whoaccepts-21",
    "info": "Moisture-wicking headband that keeps sweat out of your eyes. Lightweight and comfortable for everyday training."
},
{
    "name": "Lightweight Breathable Running Cap",
    "category": "Sports & Outdoors",
    "subcategory": "Running Essentials",
    "image": "https://m.media-amazon.com/images/I/71JWyjz2zGL._AC_SX679_.jpg",
    "url": "https://amzn.to/3YmhASv?tag=whoaccepts-21",
    "info": "Quick-dry running cap that reduces sun glare and improves comfort during warm-weather runs."
},
{
    "name": "Anti-Blister Cushioned Running Socks",
    "category": "Sports & Outdoors",
    "subcategory": "Running Essentials",
    "image": "https://m.media-amazon.com/images/I/8139KpUGwoL._AC_SX679_.jpg",
    "url": "https://amzn.to/3KY1nzY?tag=whoaccepts-21",
    "info": "Moisture-wicking running socks designed to reduce friction and prevent blisters on longer or frequent runs."
},
{
    "name": "LED Clip-On Running Safety Light",
    "category": "Sports & Outdoors",
    "subcategory": "Running Essentials",
    "image": "https://m.media-amazon.com/images/I/81W4PWCupEL._AC_SX679_.jpg",
    "url": "https://amzn.to/49fdWif?tag=whoaccepts-21",
    "info": "Compact clip-on LED light that improves visibility during early morning, evening, and winter runs."
},
{
    "name": "Reusable Soft Running Water Bottle",
    "category": "Sports & Outdoors",
    "subcategory": "Running Essentials",
    "image": "https://m.media-amazon.com/images/I/51ABfHBqJKL._AC_SX679_.jpg",
    "url": "https://amzn.to/49fUmCp?tag=whoaccepts-21",
    "info": "Lightweight collapsible soft flask that shrinks as you drink, making it ideal for short and medium training runs."
},


    {
    "name": "Lifewit Large Capacity Under Bed Storage Organiser Bags (Pack of 2)",
    "category": "Home & Kitchen",
    "season": "New Year Essentials",
    "image": "https://m.media-amazon.com/images/I/71d8uUbZSLL._AC_SX679_.jpg",
    "url": f"https://amzn.to/3YilDiF?tag={AFFILIATE_TAG}",
    "info": "Pack of 2 large 100L under-bed storage bags with reinforced handles, clear window, and sturdy zippers – breathable fabric keeps clothes, bedding, and comforters fresh and dust-free. Maximise space in smaller UK homes with easy slide-under design."
},

    {
    "name": "Mia&Coco Electric Heated Throw Blanket 120x160cm",
    "category": "Home & Kitchen",
    "season": "Winter Essentials, New Year Essentials",
    "image": "https://m.media-amazon.com/images/I/81AJ5sfPWfL._AC_SX679_.jpg",
    "url": f"https://amzn.to/3L8maAQ?tag={AFFILIATE_TAG}",
    "info": "Extra-large 120x160cm electric heated throw with 10 heat settings, 9 timer options, and machine-washable flannel fleece – ultra-soft, energy-efficient overblanket with overheat protection for cosy winter evenings on the sofa."
},

    {
    "name": "SALKING Aromatherapy Essential Oil Diffuser 500ml Ultrasonic Cool Mist Humidifier",
    "category": "Home & Kitchen",
    "season": "Winter Essentials, New Year Essentials",
    "image": "https://m.media-amazon.com/images/I/71BdaIxNUaL._AC_SX679_.jpg",
    "url": f"https://amzn.to/3MZhjCD?tag={AFFILIATE_TAG}",
    "info": "Large 500ml ultrasonic diffuser with 7-colour LED lights, 4 timer settings, and auto shut-off – creates relaxing aromatherapy mist for up to 15 hours. Quiet operation and remote control make it perfect for bedrooms, living rooms, or wellness spaces."
},
    
    {
    "name": "Utopia Towels Luxury Fluffy Bath Mat Rug 50x80cm - Grey",
    "category": "Home & Kitchen",
    "season": "New Year Essentials, Winter Essentials",
    "image": "https://m.media-amazon.com/images/I/81WVs6hbW1L._AC_SX679_.jpg",
    "url": f"https://amzn.to/3KTbvKj?tag={AFFILIATE_TAG}",
    "info": "Super soft, ultra-absorbent microfibre bath mat with non-slip rubber backing – quick-drying, machine washable, and luxuriously fluffy for instant warmth and comfort underfoot in bathrooms or bedrooms."
},

    {
    "name": "MeacoDry Arete Two 12L Dehumidifier and Air Purifier",
    "category": "Home & Kitchen",
    "season": "Winter Essentials, New Year Essentials",
    "image": "https://m.media-amazon.com/images/I/51MY3VTr3pL._AC_SX679_.jpg",
    "url": f"https://amzn.to/48Ylszg?tag={AFFILIATE_TAG}",
    "info": "Quiet 12L dehumidifier with HEPA air purifier – removes damp, mould, and allergens while drying laundry faster. Energy-efficient, ultra-quiet night mode – bestselling UK choice for healthier homes."
},
    {
    "name": "Philips Hue White Smart Bulb Twin Pack LED [B22 Bayonet Cap] – Dimmable, Bluetooth & Zigbee Compatible, Works with Alexa, Google Assistant and Apple HomeKit",
    "category": "Lighting",  # Or "Home & Kitchen" to match your existing
    "image": "https://m.media-amazon.com/images/I/71T9DZUoqhL._AC_SX679_.jpg",  # High-quality main image from similar listings
    "url": f"https://amzn.to/4pWqfaj?tag={AFFILIATE_TAG}",
    "info": "Twin pack of dimmable smart LED bulbs with soft white light, instant Bluetooth control for single-room use, or add a Hue Bridge for full features like away-from-home control and voice integration with Alexa, Google Assistant, and Apple HomeKit. Energy-efficient upgrade for mood lighting and everyday convenience in UK homes."
},

    {
    "name": "Overmont Enamelled Cast Iron Dutch Oven Casserole Dish - 5.5L Round Non-Stick Pot with Lid - Oven Safe up to 260°C - Red",
    "category": "Home & Kitchen",
    "season": "Christmas Gift Ideas, New Year Essentials",
    "image": "https://m.media-amazon.com/images/I/71fYHkEDgML._AC_SX679_.jpg",
    "url": f"https://amzn.to/4jeOuOo?tag={AFFILIATE_TAG}",
    "info": "Heavy-duty enamelled cast iron Dutch oven with excellent heat retention and even distribution — ideal for slow cooking, braising, baking bread, and one-pot meals. Oven safe to 260°C, easy-clean non-stick interior, and stylish design — bestselling affordable alternative to premium brands for home cooks."
},

    {
    "name": "TCL 32SF560 32 Inch Full HD Fire TV with Freeview Play, Dolby Audio, Voice Remote, Enhanced Brightness - Black",
    "category": "Electronics",
    "season": "Christmas Gift Ideas",
    "image": "https://m.media-amazon.com/images/I/61BYxuQ0KHL._AC_SX425_.jpg",
    "url": f"https://amzn.to/45xwjOi?tag={AFFILIATE_TAG}",
    "info": "Compact 32-inch Full HD Fire TV with built-in Alexa voice remote, Freeview Play, Dolby Audio, HDR10 support, and enhanced brightness for vivid viewing — seamless access to streaming apps like Netflix, Prime Video, and Disney+. Affordable smart TV upgrade perfect for bedrooms, kitchens, or secondary rooms."
},
{
    "name": "Ninja Foodi Max Dual Zone Air Fryer AF400UK - 9.5L",
    "category": "Home & Kitchen",
    "season": "New Year Essentials, Christmas Gift Ideas",
    "image": "https://m.media-amazon.com/images/I/519tKaMrTZL._AC_SX679_.jpg",
    "url": f"https://amzn.to/45kdy0K?tag={AFFILIATE_TAG}",
    "info": "Large 9.5L dual zone air fryer with two independent cooking baskets — cook two foods two ways simultaneously, with sync and match functions for perfect timing. Up to 75% less fat than deep frying, 6 functions including max crisp — bestselling kitchen essential for healthier family meals and quick cooking."
},
    
    {
    "name": "Ooni Karu 16 Multi-Fuel Outdoor Pizza Oven - Wood, Charcoal or Gas Fired",
    "category": "Home & Kitchen",
    "season": "Summer Essentials",
    "image": "https://m.media-amazon.com/images/I/61gq41WEf3L._AC_SX679_.jpg",
    "url": f"https://amzn.to/4sAOw7R?tag={AFFILIATE_TAG}",
    "info": "Versatile multi-fuel pizza oven reaching 950°F for authentic 60-second Neapolitan pizzas — burns wood, charcoal or gas (with optional burner). Large 16-inch cooking area, hinged door with thermometer, and premium build — bestselling choice for garden entertaining and outdoor cooking enthusiasts."
},

    {
    "name": "Apple AirPods Pro 2nd Generation - Wireless Earbuds with USB-C Charging, Active Noise Cancellation, Hearing Aid Feature, Personalised Spatial Audio",
    "category": "Electronics",
    "season": "Christmas Gift Ideas",
    "image": "https://m.media-amazon.com/images/I/61DvMw16ITL._AC_SX522_.jpg",
    "url": f"https://amzn.to/4pZnuoJ?tag={AFFILIATE_TAG}",
    "info": "Latest AirPods Pro 2 with USB-C charging, advanced active noise cancellation, adaptive audio, personalised spatial audio with head tracking, and new hearing health features — up to 6 hours listening time per charge. Premium wireless earbuds that remain the top choice for seamless iPhone integration and immersive sound."
},
    {
    "name": "Dyson V8 Advanced Cordless Vacuum Cleaner",
    "category": "Home & Kitchen",
    "season": "New Year Essentials",
    "image": "https://m.media-amazon.com/images/I/51u1PrfKc2L._AC_SX679_.jpg",
    "url": f"https://amzn.to/3MZbchx?tag={AFFILIATE_TAG}",
    "info": "Flagship Dyson V15 Detect with laser dust detection, auto-adjusting suction, LCD screen showing real-time particle count, piezo sensor, and whole-machine HEPA filtration — up to 60 minutes runtime. Premium cordless vacuum that's a top-trending gift for spotless homes and effortless cleaning."
},
    {
    "name": "Shark Stratos Cordless Pet Pro Stick Vacuum Cleaner IZ402UKTSB - Anti Hair Wrap Plus, Clean Sense IQ, DuoClean, 60min Run-Time, Removable Battery, Anti-Allergen, White/Navy",
    "category": "Home & Kitchen",
    "season": "New Year Essentials",
    "image": "https://m.media-amazon.com/images/I/615kcyMiPJL._AC_SX679_.jpg",
    "url": f"https://amzn.to/4jguATc?tag={AFFILIATE_TAG}",
    "info": "Powerful cordless stick vacuum with Clean Sense IQ (auto-adjusts suction for hidden dirt), Anti Hair Wrap Plus (removes pet/long hair from brush-roll), DuoClean floors, odour neutraliser, and anti-allergen seal — up to 60min runtime with removable battery. Bestselling upgrade for pet owners and busy homes seeking effortless, deep cleaning."
},
    {
    "name": "eufy X10 Pro Omni Robot Vacuum Cleaner With Mop, AI Obstacle Avoidance",
    "category": "Home & Kitchen",
    "season": "New Year Essentials",
    "image": "https://m.media-amazon.com/images/I/612vDNxMmtL._AC_SX679_.jpg",
    "url": f"https://amzn.to/3LoiHhx?tag={AFFILIATE_TAG}",
    "info": "Advanced robot vacuum and mop with 5500Pa suction, 3D obstacle avoidance, auto-empty station, self-washing/hot air drying mop pads, and auto-refill — keeps floors clean with minimal effort. Bestselling smart home upgrade for busy households seeking effortless cleaning and a fresh start in the new year."
},

    {
    "name": "Amazon Kindle Paperwhite (2024) - 16GB, Without Ads - Black",
    "category": "Electronics",
    "season": "Christmas Gift Ideas",
    "image": "https://m.media-amazon.com/images/I/61lwtlaSiNL._AC_SY450_.jpg",
    "url": f"https://amzn.to/4sg8fZZ?tag={AFFILIATE_TAG}",
    "info": "The fastest Kindle Paperwhite ever with a 7-inch glare-free display, higher contrast, 25% faster page turns, adjustable warm light, and up to 12 weeks of battery life — waterproof and perfect for distraction-free reading. Bestselling e-reader upgrade and ideal thoughtful gift for book lovers this Christmas."
},
{
    "name": "Echo Dot (5th generation) Smart Speaker with Alexa - Deep Sea Blue",
    "category": "Electronics",
    "season": "Christmas Gift Ideas",
    "image": "https://m.media-amazon.com/images/I/710gjg-lYyL._AC_SY741_.jpg",
    "url": f"https://amzn.to/4b7825h?tag={AFFILIATE_TAG}",
    "info": "Latest generation Echo Dot with improved audio for richer, louder sound, built-in temperature sensor, tap gestures, and Alexa voice control — perfect for music, smart home control, and daily assistance. Bestselling smart speaker that's a popular Christmas gift for all ages."
},
   
   {
    "name": "USAopoly Flip 7 Party Card Game - Ages 8+, 3+ Players, 20 Minutes Playing Time",
    "category": "Toys & Games",
    "season": "Christmas Gift Ideas",
    "image": "https://m.media-amazon.com/images/I/81m3yB192RL._AC_SX679_.jpg",
    "url": f"https://amzn.to/49xuFyE?tag={AFFILIATE_TAG}",
    "info": "Fast-paced press-your-luck card game where players flip cards without duplicates, using action cards for twists — risk it for bonus points or play safe. Addictive party fun for families and groups, quick to learn and endlessly replayable."
},
{
    "name": "LEGO Speed Champions Ferrari SF-24 F1 Race Car Toy - Model Kit with Formula 1 Driver Minifigure - Gift for 10+ Year Old Boys, Girls & Adult Motorsport Fans - 77242",
    "category": "Toys & Games",
    "season": "Christmas Gift Ideas",
    "image": "https://m.media-amazon.com/images/I/8169xVSJScL._AC_SX679_.jpg",
    "url": f"https://amzn.to/3LbsyXS?tag={AFFILIATE_TAG}",
    "info": "Authentic LEGO buildable Ferrari SF-24 F1 car from the 2024 season, complete with driver minifigure, halo cockpit, rear wing, sponsor stickers, and Pirelli tyres — perfect for recreating races or display. Trending gift for young builders and adult F1 fans alike."
},
   {
    "name": "LEGO Speed Champions Lightning McQueen Race Car Toy - Collectible Model Kit with Detailed Undercarriage - Disney Gift for 9+ Year Old Boys, Girls & Pixar Cars Movie Fans - 77255",
    "category": "Toys & Games",
    "season": "Christmas Gift Ideas",
    "image": "https://m.media-amazon.com/images/I/81f5c9hpLXL._AC_SX679_.jpg",
    "url": f"https://amzn.to/49wGjtx?tag={AFFILIATE_TAG}",
    "info": "Detailed LEGO Speed Champions build of Lightning McQueen from Disney Pixar's Cars, featuring authentic stickers, Rust-eze branding, and a unique undercarriage view — perfect for recreating movie scenes or display. Trending gift for young builders and fans celebrating the film's 20th anniversary."
},
{
    "name": "Mattel Games UNO Classic Card Game for Kids and Adults, Family Game Night, Travel Game or Gift for Kids, 2 to 10 Players, Ages 7 and Up, W2087",
    "category": "Toys & Games",
    "season": "Christmas Gift Ideas",
    "image": "https://m.media-amazon.com/images/I/71MrrNB7jCL._AC_SX679_.jpg",
    "url": f"https://amzn.to/4pUlSfT?tag={AFFILIATE_TAG}",
    "info": "The timeless matching card game where players race to discard cards by colour or number, with action cards adding twists and excitement. A family favourite for game nights, travel, or as an engaging gift — easy to learn, endlessly replayable fun for all ages."
},
   
   {
    "name": "Gritin Resistance Bands, Set of 5 Skin-Friendly Resistance Fitness Exercise Loop Bands with 5 Different Strength Levels - Carrying Case Included",
    "category": "Sports & Outdoors",
    "season": "New Year Essentials, Summer Essentials",
    "image": "https://m.media-amazon.com/images/I/617NmwvU4tL._AC_SX679_.jpg",
    "url": f"https://amzn.to/4pjWiQy?tag={AFFILIATE_TAG}",
    "info": "Set of 5 latex-free loop resistance bands in progressive strengths (extra light to extra heavy) with carry bag — skin-friendly, durable, and portable for full-body workouts. Bestselling choice for home fitness, yoga, Pilates, physio, and strength training on the go."
},

   {
    "name": "Callaway Warbird Golf Balls - 12 Pack (White)",
    "category": "Sports & Outdoors",
    "image": "https://m.media-amazon.com/images/I/71uLYL3slZL._AC_SX679_.jpg",
    "url": f"https://amzn.to/493JB64?tag={AFFILIATE_TAG}",
    "info": "High-energy core golf balls designed for maximum distance off the tee with a thin, high-sensory ionomer cover for responsive feel around the greens. Popular choice for mid-handicap golfers seeking long, straight drives and value in a durable 2-piece ball."
},
   {
    "name": "SPURK GOLF Winter Strike Mat - Fairway Protection and Practice Mat",
    "category": "Sports & Outdoors",
    "image": "https://m.media-amazon.com/images/I/61Cbx23upIL._AC_SX679_.jpg",
    "url": f"https://amzn.to/4jBhqAF?tag={AFFILIATE_TAG}",
    "info": "Durable winter golf strike mat with fairway-like turf for year-round practice — protects grass on driving ranges and allows realistic iron shots without divots. Bestselling accessory for golfers maintaining swing tempo during cold months and off-season training."
},
   
{
    "name": "From Ibiza to the Norfolk Broads: A Bowie Odyssey by James Briggs",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/61Kdkp7DPuL._SY466_.jpg",
    "url": f"https://www.amazon.co.uk/Ibiza-Norfolk-Broads-Bowie-Odyssey/dp/1837733112?tag={AFFILIATE_TAG}",
    "info": "Hilarious and heartfelt memoir of a lifelong Bowie fan cycling the iconic Life on Mars? lyric from Ibiza to the Norfolk Broads — blending travel adventure, music history, and mid-life reflection. Trending for its witty take on embracing the strange and living fearlessly like the Starman."
},
    
    {
    "name": "Always Remember by Charlie Mackesy",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/818fhGP49iL._SY385_.jpg",
    "url": f"https://amzn.to/3YOsC30?tag={AFFILIATE_TAG}",
    "info": "Heartwarming illustrated book of wisdom and comfort from the creator of The Boy, the Mole, the Fox and the Horse — a Christmas No.1 bestseller perfect for thoughtful gifting and quiet reflection."
},

{
    "name": "Guinness World Records 2026",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/8186fr4T+gL._SY425_.jpg",
    "url": f"https://amzn.to/4jheRDi?tag={AFFILIATE_TAG}",
    "info": "The iconic annual edition packed with thousands of amazing new records, facts, and photos — a perennial favourite gift for curious minds of all ages."
},
{
    "name": "The 1% Club Official Quiz Book",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/81I3J2AZbRL._SY425_.jpg",
    "url": f"https://amzn.to/4jlfWu3?tag={AFFILIATE_TAG}",
    "info": "Official companion to the hit ITV quiz show hosted by Lee Mack — packed with challenging logic puzzles and questions to test the sharpest minds at home."
},
{
    "name": "Diary of a Wimpy Kid: Partypooper by Jeff Kinney",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/91NDZEkcE7L._SY466_.jpg",
    "url": f"https://amzn.to/4pgyoVU?tag={AFFILIATE_TAG}",
    "info": "The latest hilarious instalment in the bestselling Diary of a Wimpy Kid series — perfect laugh-out-loud reading for kids and reluctant readers."
},
{
    "name": "Exit Strategy by Lee Child & Andrew Child (Jack Reacher)",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/81BL0gt7LcL._SY466_.jpg",
    "url": f"https://amzn.to/4si7U9k?tag={AFFILIATE_TAG}",
    "info": "Another gripping thriller in the iconic Jack Reacher series — high-stakes action and sharp plotting for fans of fast-paced crime fiction."
},
{
    "name": "The Secret of Secrets by Dan Brown",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/81dHhoARp9L._SY466_.jpg",
    "url": f"https://amzn.to/4aBYsaq?tag={AFFILIATE_TAG}",
    "info": "The highly anticipated new mystery thriller from the master of conspiracies — packed with codes, symbols, and globe-trotting intrigue."
},
{
    "name": "Sunrise on the Reaping by Suzanne Collins (Hunger Games)",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/71mC7kMhg6L._SY466_.jpg",
    "url": f"https://amzn.to/4avIgaJ?tag={AFFILIATE_TAG}",
    "info": "The gripping new prequel to The Hunger Games series — returning to the world of Panem with high-stakes drama and unforgettable characters."
},
{
    "name": "Onyx Storm by Rebecca Yarros (Empyrean Series)",
    "category": "Books",
    "image": "https://m.media-amazon.com/images/I/81dY-4XtCXL._SY466_.jpg",
    "url": f"https://amzn.to/48Ysbt5?tag={AFFILIATE_TAG}",
    "info": "The highly anticipated third book in the addictive romantasy Empyrean series — dragons, romance, and epic battles for fans of Fourth Wing and Iron Flame."
},
{
        "name": "Oral-B Vitality Pro Electric Toothbrush For Adults, Christmas Gifts For Him/Her, 3 Brushing Modes Including Sensitive Plus, Gentle Cleaning, 2 Min Timer, 1 Toothbrush Head, Black",
        "category": "Beauty",
        "image": "https://m.media-amazon.com/images/I/51LbAMaBpnL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Oral-B-Vitality-Toothbrush-Including-Sensitive/dp/B0B18V92KS?tag={AFFILIATE_TAG}",
        "info": "Affordable electric toothbrush with 3 brushing modes including Sensitive Plus for gentle cleaning, 2-minute timer, and superior plaque removal vs manual brushing. Bestselling entry-level Oral-B model for everyday oral care and healthier gums."
    },
    {
        "name": "The Impossible Fortune by Richard Osman (Thursday Murder Club 5)",
        "category": "Books",
        "image": "https://m.media-amazon.com/images/I/71eTwnmHa3L._SY466_.jpg",
        "url": f"https://www.amazon.co.uk/Impossible-Fortune-multi-million-bestselling-Thursday/dp/0241743982?tag={AFFILIATE_TAG}",
        "info": "The latest cosy crime bestseller in the multi-million selling Thursday Murder Club series — perfect for fans of clever, heartwarming murder mysteries."

},
    {
    "name": "Catsan Hygiene Plus Non-Clumping Cat Litter, 100% Natural White Hygiene Granules, Odour Control, 20 L",
    "category": "Pet Supplies",
    "image": "https://m.media-amazon.com/images/I/71bURZaHfFL._AC_SX425_.jpg",
    "url": f"https://www.amazon.co.uk/Catsan-Hygiene-Plus-Litter-White/dp/B001MZV3OO?tag={AFFILIATE_TAG}",
    "info": "Non-clumping white hygiene cat litter made from natural quartz sand and lime — highly absorbent, locks in odours, and prevents bacterial growth for superior freshness. UK's leading choice for clean, hygienic litter trays and happy cats."
},
    {
    "name": "HotHands Hand Warmers - Up to 10 Hours of Heat - 40 Pairs - Air Activated, Odourless, Natural & Safe",
    "category": "Sports & Outdoors",
    "season": "Winter Essentials",
    "image": "https://m.media-amazon.com/images/I/71SBcNUrFCL._AC_SX679_.jpg",
    "url": f"https://www.amazon.co.uk/HOTHANDS-Hand-Warmers-Pairs-activated/dp/B08GCT8SXZ?tag={AFFILIATE_TAG}",
    "info": "Air-activated hand warmers providing up to 10 hours of natural, odourless heat — safe, easy to use, and perfect for cold weather activities, commuting, or outdoor events. Bestselling essential for staying warm during winter walks, sports, or festivals."
},
    {
    "name": "Fitbit Charge 6 Activity Tracker with 6 months of Fitbit Premium Included, Heart Rate, GPS, Health Tools, Sleep Tracking, Readiness Score and More - Obsidian/Black",
    "category": "Sports & Outdoors",
    "image": "https://m.media-amazon.com/images/I/61AeGQhwjxL._AC_SX679_.jpg",
    "url": f"https://www.amazon.co.uk/Fitbit-Activity-6-months-Membership-Readiness/dp/B0B6WRFY5S?tag={AFFILIATE_TAG}",
    "info": "Advanced fitness tracker with built-in GPS, heart rate monitoring, sleep tracking, stress management, and a daily Readiness Score — includes 6 months Premium membership. Popular choice for active lifestyles, workout motivation, and overall health insights in everyday routines."
},
    {
    "name": "WaterWipes Sensitive+ Newborn & Baby Wipes, 720 Count (12 Packs), 3-In-1 Cleans, Cares, Protects, 99.9% Water, Unscented",
    "category": "Baby",
    "image": "https://m.media-amazon.com/images/I/81OT3srjQiL._AC_SX679_PIbundle-12,TopRight,0,0_SH20_.jpg",
    "url": f"https://www.amazon.co.uk/WaterWipes-Sensitive-Newborn-Biodegradable-Unscented/dp/B08MXSBRSB?tag={AFFILIATE_TAG}",
    "info": "Gentle baby wipes made with 99.9% purified water and a drop of fruit extract — plastic-free, unscented, and dermatologist-approved for sensitive newborn skin, including eczema-prone. UK's top choice for pure, effective cleansing that cares for and protects delicate skin every day."
},
    {
    "name": "Mens Two Tone Memory Foam Slippers Mule Slip On Comfortable Hard Sole Non Slip Slippers for Men",
    "category": "Fashion",
    "image": "https://m.media-amazon.com/images/I/81EEfuhlShL._AC_SY695_.jpg",
    "url": f"https://www.amazon.co.uk/Mens-Two-Tone-Memory-Foam-Slipper/dp/B07CLXD2V4?tag={AFFILIATE_TAG}",
    "info": "Cosy two-tone memory foam slippers with hard non-slip sole and mule design — perfect for indoor comfort and quick outdoor trips. Bestselling men's slippers for all-day warmth, support, and durability during colder months."
},
    {
    "name": "More or Less: The Game of Judgement & Outlandish Guesstimation",
    "category": "Toys & Games",
    "season": "Christmas Gift Ideas",
    "image": "https://m.media-amazon.com/images/I/71i5j54tKVL._AC_SX679_.jpg",
    "url": f"https://www.amazon.co.uk/More-Less-Judgement-Outlandish-Guesstimation/dp/B087KLKN7T?tag={AFFILIATE_TAG}",
    "info": "Hilarious party game where players guess whether random facts are 'more' or 'less' than a given number — perfect for family gatherings, parties, and game nights. Trending for its mix of ridiculous questions, laughs, and surprising knowledge."
},
    {
        "name": "Catching Sticks Games, Falling Sticks Catching Game, Drop It Catch It Win It Reaction Game",
        "category": "Toys & Games",
        "image": "https://m.media-amazon.com/images/I/71dAXELqizL._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/Catching-Reaction-Reactions-Coordination-Christmas/dp/B0FMD3DXPC?tag={AFFILIATE_TAG}",
        "info": "Fast-paced reaction game where colorful sticks drop randomly at adjustable speeds — players race to catch them, building hand-eye coordination and quick reflexes. Viral trending Christmas gift for kids and families, perfect for parties and screen-free fun."
    },
    {
        "name": "WOQQW Back Massager with Heat, Shiatsu Back and Neck Massager, Deeper Tissue Kneading Massage Pillow for Shoulder, Leg, Foot, Body",
        "category": "Health & Personal Care",
        "season": "Christmas Gift Ideas",
        "image": "https://m.media-amazon.com/images/I/81fiFvLzZ1L._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/Massager-Shiatsu-Kneading-Massage-Shoulder/dp/B08MYSL6T8?tag={AFFILIATE_TAG}",
        "info": "Shiatsu massage pillow with deep-kneading nodes and soothing heat function — versatile for neck, back, shoulders, legs, and feet to relieve muscle tension and promote relaxation. Popular wellness gift for stress relief during the holiday season and beyond."
    },
    {
        "name": "SHOKZ OpenFit Air Open-Ear Headphones, True Wireless Bluetooth Earphones with Mic, Fast Charging, 28h Playtime, IP54 Waterproof for Workout - Black",
        "category": "Electronics",
        "image": "https://m.media-amazon.com/images/I/61eNpp4eTlL._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/SHOKZ-Headphones-Bluetooth-Earphones-Waterproof-Black/dp/B0CRTM6B55?tag={AFFILIATE_TAG}",
        "info": "Open-ear true wireless headphones with secure fit, situational awareness, powerful bass, and long battery life — ideal for workouts, running, or daily use without blocking ambient sound. Trending choice for active lifestyles and safer outdoor listening."
    },
    {
        "name": "Shot in the Dark: The Ultimate Unorthodox Quiz Game",
        "category": "Toys & Games",
        "season": "Christmas Gift Ideas",
        "image": "https://m.media-amazon.com/images/I/71BXgJpJ0oL._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/Shot-Dark-Christmas-Ultimate-Unorthodox/dp/B08LFY1F42?tag={AFFILIATE_TAG}",
        "info": "Hilarious card-based quiz game with bizarre, obscure questions where nobody knows the answer — players guess, and the best (or funniest) guess wins points. Perfect screen-free entertainment for Christmas parties, family gatherings, and game nights with all ages."
    },
    {
        "name": "VonShef 3 Tray Buffet Server & Hot Plate Food Warmer",
        "category": "Home & Kitchen",
        "image": "https://m.media-amazon.com/images/I/71kTQECp3FL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/VonShef-Tray-Warmer-Buffet-Server/dp/B073Q5G9VX?tag={AFFILIATE_TAG}",
        "info": "3-tray electric buffet server with adjustable temperature — keeps food warm for parties, hosting, or family meals. Top trending choice for holiday entertaining with easy clean trays."
    },
    {
        "name": "Driving Theory Test Kit UK 2025 with Highway Code Book",
        "category": "Books",
        "image": "https://m.media-amazon.com/images/I/81akIVih9NL._SY385_.jpg",
        "url": f"https://www.amazon.co.uk/UK-Driving-Theory-Test-Kit/dp/B09D84M7C4?tag={AFFILIATE_TAG}",
        "info": "Complete 2025 theory test kit with official Highway Code book, practice questions, hazard perception — essential for passing the UK driving test. Massive demand spike for new learners."
    },
    {
        "name": "Magnetic Chess Game with Stones Portable Family Board",
        "category": "Toys & Games",
        "image": "https://m.media-amazon.com/images/I/61mcbNi2MGL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Magnetic-Training-Chesss-Birthdays-Gatherings/dp/B0FMXLG87Y?tag={AFFILIATE_TAG}",
        "info": "Portable magnetic chess set with stones and ropes — fun family game for parties, travel, or gatherings. Addictive strategy challenge that's trending for all ages."
    },
    {
        "name": "Magnesium Glycinate 3-in-1 Complex 1800mg Capsules",
        "category": "Health & Personal Care",
        "image": "https://m.media-amazon.com/images/I/717wIpxmJdL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Magnesium-Glycinate-Complex-Supplements-Bisglycinate/dp/B0C9VVCL12?tag={AFFILIATE_TAG}",
        "info": "High-absorption 3-in-1 magnesium (glycinate, citrate, malate) — supports sleep, muscle recovery, energy, and stress relief. Consistent bestseller for wellness routines."
    },
    {
        "name": "[Built-in Apps & Android 11.0] Mini Projector Portable 20000 Lux 4K Supported",
        "category": "Electronics",
        "image": "https://m.media-amazon.com/images/I/61FJ2edQURL._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/Projector-Portable-Supported-Rotation-Compatible/dp/B0FMR73KL2?tag={AFFILIATE_TAG}",
        "info": "Compact portable projector with Android 11, built-in apps, 180° rotation, auto keystone — perfect for home cinema, outdoor movies, or gaming. High brightness and compatibility make it a top trending choice."
    },
    {
        "name": "Gezqieunk Christmas Jumper Women Xmas Printed Sweatshirt",
        "category": "Fashion",
        "season": "Christmas Gift Ideas",
        "image": "https://m.media-amazon.com/images/I/61Tm7Sqg13L._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Gezqieunk-Christmas-Sweatshirts-Crewneck-Sweaters/dp/B0FXF94VW8?tag={AFFILIATE_TAG}",
        "info": "Festive oversized jumper with fun Christmas prints — perfect cosy gift, surging in popularity for holiday parties and family photos."
    },
    {
        "name": "Karaoke Machine for Kids with Microphone",
        "category": "Toys & Games",
        "image": "https://m.media-amazon.com/images/I/81QJgWZmfyL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Kids-Karaoke-Machine-Birthday-Girls-Pink/dp/B0DK4NL37F?tag={AFFILIATE_TAG}",
        "info": "Mini karaoke set with lights, Bluetooth, and mic — top Christmas gift for kids, massive sales spike for family sing-alongs."
    },
    {
        "name": "L’Oréal Paris Revitalift Laser Anti-Ageing Day Cream",
        "category": "Beauty",
        "image": "https://m.media-amazon.com/images/I/41uhhU1DU7L._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/LOreal-Paris-Revitalift-Pro-Xylane-Anti-Ageing/dp/B00SNOAZM8?tag={AFFILIATE_TAG}",
        "info": "Triple-action cream reduces wrinkles and firms skin — huge mover in beauty for gifting season and self-care routines."
    },
    {
        "name": "OCOOPA Magnetic Hand Warmers Rechargeable 2 Pack",
        "category": "Sports & Outdoors",
        "season": "Christmas Gift Ideas, Winter Essentials",
        "image": "https://m.media-amazon.com/images/I/61sa5Gx+ZQL._AC_SY300_SX300_QL70_ML2_.jpg",
        "url": f"https://www.amazon.co.uk/OCOOPA-Magnetic-Rechargeable-Handwarmers-Certified/dp/B0CH34CB3P?tag={AFFILIATE_TAG}",
        "info": "Portable, double-sided heat with magnetic design — essential for cold UK winter walks, commuters, and outdoor events."
    },
    {
        "name": "Herd Mentality Board Game",
        "category": "Toys & Games",
        "image": "https://m.media-amazon.com/images/I/61jvW6xtkdL._AC_SY300_SX300_QL70_ML2_.jpg",
        "season": "Christmas Gift Ideas",
        "url": f"https://www.amazon.co.uk/Herd-Mentality-Board-Game-Addictive/dp/B09S3YBBRR?tag={AFFILIATE_TAG}",
        "info": "Hilarious party game where you try to think like the herd — perfect family/party entertainment, flying off shelves for Christmas."
    },
    {
        "name": "Amazon Fire TV Stick 4K",
        "category": "Electronics",
        "image": "https://m.media-amazon.com/images/I/61TzK204IjL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/Amazon-Fire-TV-Stick-4K/dp/B08XVYZ1Y5?tag={AFFILIATE_TAG}",
        "info": "Stream 4K content with Dolby Vision and Alexa voice control — top gift for movie lovers and home entertainment upgrades."
    }

    
]
# ---------------- BLOG SECTION ---------------- #
BLOG_POSTS = {
    "8-essential-home-products-to-upgrade-your-space-in-2026": {
        "title": "8 Essential Home Products to Upgrade Your Space in 2026",
        "description": "Discover trending home upgrades for 2026 – smart devices, cozy textiles, and practical essentials to refresh your UK home affordably.",
        "heading": "8 Essential Home Upgrades for 2026",
        "subtitle": "Trending Amazon picks to make your space smarter, cozier, and more efficient this year.",
        "content": """
            <article style="max-width:900px;margin:40px auto;line-height:1.8;font-size:1.1rem;color:#fff;">
                <p>As we step into 2026, many UK households are looking for simple, affordable ways to refresh their living spaces. From energy-saving tech to cozy comforts, here are 8 essential home products trending right now on Amazon.</p>
                
                <h2>1. Philips Hue Smart Bulbs</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/philips-hue-white-smart-bulb-twin-pack-led-b22-bayonet-cap--dimmable-bluetooth--and--zigbee-compatible-works-with-alexa-google-assistant-and-apple-homekit">
        <img src="https://m.media-amazon.com/images/I/71T9DZUoqhL._AC_SX679_.jpg" alt="Philips Hue Smart Bulbs" loading="lazy" style="border-radius:16px;">
    </a>
    <p>Control lighting from your phone, set moods, and save energy – perfect starter smart home upgrade.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
    <a href="/product/philips-hue-white-smart-bulb-twin-pack-led-b22-bayonet-cap--dimmable-bluetooth--and--zigbee-compatible-works-with-alexa-google-assistant-and-apple-homekit">
        <button>View Details & Buy</button>
    </a> <a href="https://amzn.to/4pWqfaj?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Lighting', 'event_label': 'Philips Hue Twin Pack', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <h2>2. Ninja Foodi Max Dual Zone Air Fryer AF400UK - 9.5L</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/ninja-foodi-max-dual-zone-air-fryer-af400uk-9-5l">
        <img src="https://m.media-amazon.com/images/I/519tKaMrTZL._AC_SX679_.jpg" 
             alt="Ninja Foodi Max Dual Zone Air Fryer 9.5L – two independent cooking zones" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Large 9.5L dual-zone air fryer lets you cook two different foods two ways at once and finish at the same time with Sync. Up to 75% less fat than deep frying, 6 functions (air fry, roast, bake, reheat, dehydrate, max crisp) – perfect for quick, healthier family meals.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/ninja-foodi-max-dual-zone-air-fryer-af400uk-9-5l">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/45kdy0K?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'Ninja Dual Zone Air Fryer', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <h2>3. MeacoDry Arete Two 12L Dehumidifier and Air Purifier</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/meacodry-arete-two-12l-dehumidifier-and-air-purifier">
        <img src="https://m.media-amazon.com/images/I/51MY3VTr3pL._AC_SX679_.jpg" 
             alt="MeacoDry Arete Two 12L Dehumidifier with HEPA air purification" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Quiet, energy-efficient 12L dehumidifier with built-in HEPA air purifier – perfect for UK homes battling damp, mould, and allergies. Extracts up to 12 litres per day, dries laundry faster, runs ultra-quiet in night mode, and purifies air for healthier breathing all year round.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/meacodry-arete-two-12l-dehumidifier-and-air-purifier">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/49hEeAD?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'MeacoDry Arete Two 12L', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <h2>4. Utopia Towels Luxury Fluffy Bath Mat Rug (50x80cm)</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/utopia-towels-luxury-fluffy-bath-mat-rug-50x80cm---grey">
        <img src="https://m.media-amazon.com/images/I/81WVs6hbW1L._AC_SX679_.jpg" 
             alt="Utopia Towels Luxury Fluffy Grey Bath Mat – soft microfibre rug" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Instant warmth underfoot with non-slip, quick-dry designs. Super-absorbent microfibre that's machine washable and luxuriously plush – bestselling upgrade for cosy bathrooms without the premium price tag.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/utopia-towels-luxury-fluffy-bath-mat-rug-50x80cm---grey">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/4si7AHt?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'Utopia Fluffy Bath Mat', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
               <h2>5. SALKING Aromatherapy Essential Oil Diffuser 500ml</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/salking-aromatherapy-essential-oil-diffuser-500ml-ultrasonic-cool-mist-humidifier">
        <img src="https://m.media-amazon.com/images/I/71BdaIxNUaL._AC_SX679_.jpg" 
             alt="SALKING 500ml Aromatherapy Diffuser with LED lights and remote" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Create a relaxing spa atmosphere at home with calming scents. Large 500ml capacity runs up to 15 hours with quiet ultrasonic mist, 7 soothing LED colours, 4 timers, remote control, and auto shut-off – ideal for better sleep, stress relief, and wellness routines.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/salking-aromatherapy-essential-oil-diffuser-500ml-ultrasonic-cool-mist-humidifier">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/3MZhjCD?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'SALKING Aromatherapy Diffuser', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <h2>6. Mia&Coco Electric Heated Throw Blanket 120x160cm</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/mia-and-coco-electric-heated-throw-blanket-120x160cm">
        <img src="https://m.media-amazon.com/images/I/81AJ5sfPWfL._AC_SX679_.jpg" 
             alt="Mia&Coco Electric Heated Throw Blanket – large cosy fleece overblanket" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Stay cozy on the sofa while cutting heating bills. Extra-large 120x160cm flannel fleece throw with 10 heat levels, 9 auto-off timers, machine washable design, and overheat protection – bestselling energy-saving essential for UK winters.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/mia-and-coco-electric-heated-throw-blanket-120x160cm">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/3YmgAhc?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'Mia&Coco Heated Throw', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <h2>7. Dyson Detect Advanced Cordless Vacuum Cleaner</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/dyson-v8-advanced-cordless-vacuum-cleaner">
        <img src="https://m.media-amazon.com/images/I/51u1PrfKc2L._AC_SX679_.jpg" 
             alt="Dyson V15 Detect Cordless Vacuum with laser dust detection" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Effortless daily cleaning with laser dust detection, auto-adjusting suction, and HEPA filtration – huge time-saver for busy homes. Reveals invisible dust, deep cleans carpets and hard floors, and runs up to 60 minutes.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/dyson-v8-advanced-cordless-vacuum-cleaner">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/3MZbchx?tag=whoaccepts-21" target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'Dyson V15 Detect', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <h2>8. Lifewit Large Capacity Under Bed Storage Organiser Bags (Pack of 2)</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/lifewit-large-capacity-under-bed-storage-organiser-bags-pack-of-2">
        <img src="https://m.media-amazon.com/images/I/71d8uUbZSLL._AC_SX679_.jpg" 
             alt="Lifewit Under Bed Storage Bags – large capacity organisers for clothes and bedding" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Maximise space in smaller UK properties without clutter. Pack of 2 extra-large 100L bags with clear windows, reinforced handles, and breathable fabric – perfect for storing seasonal clothes, duvets, or toys neatly under the bed.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/lifewit-large-capacity-under-bed-storage-organiser-bags-pack-of-2">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/49fUzWa?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'Lifewit Under Bed Storage', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <p>All these products are available with fast delivery. Start your 2026 home refresh today!</p>
            </article>
        """
    }




   


    # Add more posts here later
}

# ---------------- THEMES ---------------- #
THEMES = [
    {
        "bg": "#0f172a",
        "card": "#1e293b",
        "accent": "#38bdf8",
        "button": "#0284c7",
        "tag": "#7dd3fc",
        "text_accent": "#bae6fd",
        "gradient": "linear-gradient(90deg,#0284c7,#38bdf8)"
    }
]

def get_daily_theme():
    return THEMES[datetime.date.today().timetuple().tm_yday % len(THEMES)]

# ---------------- IMPROVED AI HOOK ---------------- #
def generate_hook(name):
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"""
Write a calm, elegant 1–2 sentence description explaining why this product is popular among UK shoppers.
Focus on its practical benefits, quality, or appeal in daily life.
Vary the phrasing across different products — avoid repeating common words like "staple", "essential", or "go-to".
Use <b> tags subtly for key features.
End with a complete sentence.
Product: {name}
"""
            }],
            temperature=0.7,
            max_tokens=120
        )
        hook = r.choices[0].message.content.strip()
        hook = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', hook)
        if not re.search(r'[.!?]$', hook):
            hook += " among UK shoppers."
        return hook
    except Exception as e:
        print(f"Groq error: {e}")
        return "A popular choice among UK shoppers for its quality and everyday appeal."

# ---------------- STORAGE ---------------- #
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def enrich_products(products):
    enriched = []
    for p in products:
        p_copy = dict(p)
        p_copy["hook"] = generate_hook(p["name"])
        enriched.append(p_copy)
    return enriched

def refresh_products(background=False):
    today = str(datetime.date.today())
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            cache = json.load(f)
            if cache.get("date") == today:
                return cache["products"]

    def do_refresh():
        enriched = enrich_products(PRODUCTS)
        with open(CACHE_FILE, "w") as f:
            json.dump({"date": today, "products": enriched}, f)
        history = load_history()
        history[today] = enriched
        save_history(history)

    if background:
        Thread(target=do_refresh).start()
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as f:
                cached = json.load(f).get("products", [])
                if cached:
                    return cached
        return [{"name": p["name"], "category": p["category"], "image": p["image"],
                 "url": p["url"], "info": p["info"], "hook": p["info"]} for p in PRODUCTS]
    else:
        do_refresh()
        with open(CACHE_FILE) as f:
            return json.load(f)["products"]

# ---------------- HELPERS ---------------- #
def slugify(text):
    text = text.lower()
    text = re.sub(r'&', '-and-', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    return text

def get_categories(history):
    today_str = str(datetime.date.today())
    today_products = history.get(today_str, PRODUCTS)
    
    cats = set()
    parent_sub_map = {}  # sub -> parent
    
    for p in today_products:
        cats.add(p["category"])
        if "subcategory" in p:
            parent_sub_map[p["subcategory"]] = p["category"]
        if "season" in p:
            for s in p["season"].split(","):
                stripped = s.strip()
                if stripped:
                    cats.add(stripped)
    
    combined = sorted(cats)
    for sub in sorted(parent_sub_map):
        parent = parent_sub_map[sub]
        combined.append(f"{parent} > {sub}")
    
    return combined

def paginate(items, page):
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return items[start:end], len(items)

def shorten_product_name(name, max_length=80):
    if len(name) <= max_length:
        return name
    
    if ',' in name:
        shortened = name.split(',', 1)[0].strip()
        if len(shortened) <= max_length:
            return shortened
    
    if '(' in name:
        shortened = name.split('(', 1)[0].strip()
        if len(shortened) <= max_length:
            return shortened
    
    words = name.split()
    shortened = ''
    for word in words:
        if len(shortened + ' ' + word) <= max_length - 3:
            shortened += (' ' + word) if shortened else word
        else:
            break
    return shortened + '...'

def ensure_hook(p):
    # If hook is missing or fallback, regenerate
    if "hook" not in p or p["hook"] == p.get("info") or "well-regarded product" in p["hook"]:
        p["hook"] = generate_hook(p["name"])
    return p

# ---------------- CSS ---------------- #
CSS_TEMPLATE = """<style>
body{margin:0;background:{{bg}};color:#fff;font-family:'Outfit',sans-serif;padding:20px 20px 40px}
h1{text-align:center;font-size:3rem;background:{{gradient}};-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:40px 0 10px}
.subtitle{text-align:center;opacity:.85;max-width:900px;margin:20px auto;color:{{text_accent}};font-size:1.1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;max-width:1400px;margin:auto}
.card{background:{{card}};border-radius:22px;padding:20px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.6);transition:transform .3s,box-shadow .3s}
.card:hover{transform:translateY(-8px);box-shadow:0 30px 60px rgba(0,0,0,.7)}
img{width:100%;border-radius:16px;margin:16px 0}
.tag{background:{{tag}};padding:6px 14px;border-radius:20px;font-size:.85rem;display:inline-block;margin-bottom:12px}
button{
    background:{{button}};
    border:none;
    padding:16px 36px;
    border-radius:50px;
    font-size:1.1rem;
    font-weight:900;
    color:white;
    cursor:pointer;
    transition:.3s;
    animation: pulse 2.5s infinite ease-in-out;
}
button:hover{
    opacity:.9;
    transform:scale(1.05);
    animation:none;
}
@keyframes pulse{
    0%{box-shadow:0 0 0 0 rgba(2,132,199,0.4);}
    70%{box-shadow:0 0 0 12px rgba(2,132,199,0);}
    100%{box-shadow:0 0 0 0 rgba(2,132,199,0);}
}
@media (prefers-reduced-motion: reduce){
    button{animation:none;}
}
footer{text-align:center;opacity:.7;margin:80px 0 40px;font-size:.9rem;line-height:1.6}
a{color:{{text_accent}};text-decoration:none}
nav{background:{{card}};padding:16px;margin:20px 0 40px;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.4);text-align:center}
nav a{margin:0 16px;color:{{text_accent}};font-weight:700;font-size:1.1rem;transition:.2s}
nav a:hover{opacity:.8}
.pagination{display:flex;justify-content:center;gap:16px;margin:40px 0}
.pagination a{background:{{button}};padding:10px 16px;border-radius:12px;color:white;text-decoration:none;font-weight:700;transition:.2s}
.pagination a:hover{opacity:.9}
.loading{text-align:center;opacity:.8;margin:80px 0;font-size:1.3rem;color:{{text_accent}};}
@media (max-width:768px){
    nav a{margin:0 10px;font-size:1rem}
    .grid{grid-template-columns:1fr}
}

/* Single product page - center card & constrain image */
.grid:has(> .card:only-child) .card {
    max-width: 600px;
    margin: 0 auto;
}
.grid:has(> .card:only-child) img {
    max-width: 500px;
    width: 100%;
    height: auto;
    margin: 20px auto;
    display: block;
    border-radius: 16px;
}

/* Uniform titles & aligned images */
.card h2 {
    min-height: 70px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 12px 0;
    font-size: 1.25rem;
    line-height: 1.3;
    font-weight: 900;
}

.card img {
    width: 100%;
    max-height: 380px;
    object-fit: contain;
    background: #111827;
    border-radius: 16px;
    margin: 16px 0;
}

/* Button & "More" spacing */
.card > a[onclick] {
    margin: 20px 0 10px;
}
.card p:last-of-type {
    margin: 10px 0;
    font-size: .85rem;
    opacity: .7;
}
</style>"""

# ---------------- HTML TEMPLATE ---------------- #
BASE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="google-site-verification" content="ZDatY7MyS9eDAYQB97mQ_dxlAv2dgd2IqG1kPg82imU" />
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title>
<meta name="description" content="{{ description }}">
<link rel="canonical" href="{{ canonical_url }}">
{% if next_page_url %}
<link rel="next" href="{{ next_page_url }}">
{% endif %}
{% if prev_page_url %}
<link rel="prev" href="{{ prev_page_url }}">
{% endif %}
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-C1YNKZS6PG"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-C1YNKZS6PG');
</script>
<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ description }}">
<meta property="og:type" content="website">
<meta property="og:url" content="{{ canonical_url }}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">
{{ css|safe }}
</head>
<body>

<nav>
    <a href="/">Home</a>
    <a href="/blog">Blog</a>
    {% for cat in categories %}
    <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
    {% endfor %}
</nav>

<h1>{{ heading }}</h1>
<p class="subtitle">{{ subtitle }}</p>

<p style="text-align:center;opacity:.7;margin-bottom:40px;">
✔ UK-focused · ✔ Updated daily · ✔ Thoughtfully curated gifts
</p>

{% if products %}
<div class="grid">
{% for p in products %}
<div class="card">
    <span class="tag">
    {{ p.category }}{% if "subcategory" in p %} > {{ p.subcategory }}{% endif %}
    </span>
    <a href="/product/{{ slugify(p.name) }}">
        <h2>{{ shorten_product_name(p.name) }}</h2>
    </a>

    <a href="/product/{{ slugify(p.name) }}">
        <img src="{{ p.image }}" alt="{{ p.name }} – {{ p.info }}" loading="lazy">
    </a>

    <p>{{ p.hook|safe }}</p>

   <script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{{ shorten_product_name(p.name) }}",
  "image": "{{ p.image }}",
  "description": "{{ p.info }}",
  "url": "{{ p.url }}",
  "brand": {"@type": "Brand", "name": "{{ p.brand or 'Various' }}"},
  "offers": {
    "@type": "Offer",
    "url": "{{ p.url }}",
    "availability": "https://schema.org/InStock",
    "seller": {
      "@type": "Organization",
      "name": "Amazon"
    }
  }
}
</script>



<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "{{ SITE_URL }}/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "{{ p.category }}",
      "item": "{{ SITE_URL }}/category/{{ slugify(p.category) }}"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "{{ shorten_product_name(p.name) }}"
    }
  ]
}
</script>


    <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored" 
       aria-label="View {{ p.name }} on Amazon"
       onclick="gtag('event', 'affiliate_click', { 
           'event_category': '{{ p.category }}', 
           'event_label': '{{ p.name }}', 
           'value': 1,
           'page_path': window.location.pathname
       });">
        <button>View on Amazon</button>
    </a>

        <p style="font-size:.85rem;opacity:.7;margin-top:16px;">
        More <a href="/category/{{ slugify(p.category + (' > ' + p.subcategory if 'subcategory' in p else '')) }}">
            {{ p.category }}{% if "subcategory" in p %} > {{ p.subcategory }}{% endif %}
        </a> gifts
    </p>
</div>
{% endfor %}
</div>

{# === RELATED PRODUCTS SECTION (only shows on single product pages) === #}

<h2 style="text-align:center;margin:60px 0 20px;font-size:2rem;background:{{gradient}};-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
    More Popular {{ related_products[0].category if related_products else 'UK' }} Gifts
</h2>

{% if related_products %}
<div class="grid">
    {% for rp in related_products %}
    <div class="card">
        <span class="tag">{{ rp.category }}</span>
        <a href="/product/{{ slugify(rp.name) }}">
            <h2>{{ shorten_product_name(rp.name) }}</h2>
        </a>
        <a href="/product/{{ slugify(rp.name) }}">
            <img src="{{ rp.image }}" alt="{{ rp.name }} – {{ rp.info }}" loading="lazy">
        </a>
        <p>{{ rp.hook|safe }}</p>
        <a href="{{ rp.url }}" target="_blank" rel="nofollow sponsored" 
           aria-label="View {{ rp.name }} on Amazon">
            <button>View on Amazon</button>
        </a>
    </div>
    {% endfor %}
</div>
{% else %}
<p style="text-align:center;opacity:.7;">Check out more top gifts across the UK!</p>
{% endif %}



{% else %}
<p class="loading">
    Loading today's gifts...<br>
    <small>Generating fresh AI descriptions – this only happens once per day.</small>
</p>
{% endif %}

<footer>
    <p><strong>As an Amazon Associate, I earn from qualifying purchases.</strong></p>
    <p>FyboBuybo is an independent UK gifts site. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates.</p>
</footer>

</body>
</html>
"""

# ---------------- ROUTES ---------------- #
def render_page(title, description, heading, subtitle, products, page=1, page_url=lambda p: "#", related_products=None):
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    history = load_history()
    categories = get_categories(history)
    canonical = SITE_URL + request.path
    page_num = int(request.args.get("page", 1))
    if page_num > 1:
        canonical += f"?page={page_num}"

    paged_products, total_items = paginate(products, page)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    # ---------------- Pagination rel links ---------------- #
    next_page_url = page_url(page + 1) if page < total_pages else None
    prev_page_url = page_url(page - 1) if page > 1 else None

    return render_template_string(
        BASE_HTML,
        title=title,
        description=description,
        heading=heading,
        subtitle=subtitle,
        products=paged_products,
        categories=categories,
        css=css,
        canonical_url=canonical,
        SITE_URL=SITE_URL,
        slugify=slugify,
        shorten_product_name=shorten_product_name,
        related_products=related_products or [],
        total_pages=total_pages,
        page=page,
        page_url=page_url,
        button=theme["button"],
        next_page_url=next_page_url,
        prev_page_url=prev_page_url
    )


@app.route("/")
def home():
    products = refresh_products(background=False)[:ITEMS_PER_PAGE]
    return render_page(
        title="FyboBuybo – Trending UK Gifts & Popular Presents",
        description="Discover today's trending UK gifts and popular presents across toys, beauty, electronics and more. Independently curated and refreshed daily.",
        heading="FyboBuybo – Trending UK Gifts",
        subtitle="A curated selection of popular gifts and presents, refreshed daily.",
        products=products
    )

@app.route("/category/<slug>")
def category(slug):
    history = load_history()
    unique_products = {}
    
    # Decode possible "parent-sub" format
    if ">" in slug.replace("--", " "):  # Handle slugified "sports--and--outdoors-running-essentials"
        parts = [part.strip() for part in slug.replace("--", "-").split("-") if part]
        potential_sub = parts[-1] if len(parts) > 1 else None
    else:
        potential_sub = None
    
    for day in history.values():
        for p in day:
            match = False
            if slugify(p["category"]) == slug:
                match = True
            elif "season" in p and any(slugify(s.strip()) == slug for s in p["season"].split(",")):
                match = True
            elif "subcategory" in p and slugify(p["subcategory"]) == slug:
                match = True
            # New: Match combined parent-sub slug
            elif "subcategory" in p and slugify(f"{p['category']} {p['subcategory']}") == slug:
                match = True
            
            if match:
                key = p["name"] + p["url"]
                unique_products[key] = p
    
    products = [ensure_hook(p) for p in unique_products.values()]
    
    if not products:
        abort(404)
    
    # Display name logic (improve for subcats)
    if ">" in slug:
        cat_name = slug.replace("--", " > ").replace("-", " ").title()
    else:
        cat_name = slug.replace("-", " ").title()
    
    # ... rest unchanged

    def page_url(p):
        return url_for("category", slug=slug, page=p)

    page = int(request.args.get("page", 1))
    return render_page(
        title=f"{cat_name} – FyboBuybo",
        description=f"Explore popular {cat_name.lower()} in the UK, featuring trending gifts and bestsellers.",
        heading=cat_name,
        subtitle=f"Hand-picked selection of {cat_name.lower()}, updated daily.",
        products=products,
        page=page,
        page_url=page_url
    )


@app.route("/product/<path:product_slug>")
def product_detail(product_slug):
    decoded_slug = product_slug.replace("-", " ").lower()

    history = load_history()
    today_str = str(datetime.date.today())
    all_days = history.copy()
    today_products = refresh_products(background=True)
    all_days[today_str] = today_products

    found_product = None
    for day_prods in all_days.values():
        for p in day_prods:
            if slugify(p["name"]) == product_slug:
                found_product = ensure_hook(p)
                break
        if found_product:
            break

    if not found_product:
        abort(404)

    # ---------------- Related products ----------------
    related = []
    for day_prods in all_days.values():
        for p in day_prods:
            if p["category"] == found_product["category"] and p["name"] != found_product["name"]:
                related.append(ensure_hook(p))

    # Remove duplicates and limit to 6
    related = list({p["name"] + p["url"]: p for p in related}.values())[:6]

    # Fallback: if no related products, show other popular items from the same season
    if not related and "season" in found_product:
        for day_prods in all_days.values():
            for p in day_prods:
                if p["name"] != found_product["name"] and any(
                    s.strip() in p.get("season", "") for s in found_product["season"].split(",")
                ):
                    related.append(ensure_hook(p))
        related = list({p["name"] + p["url"]: p for p in related}.values())[:6]

    return render_page(
        title=f"{shorten_product_name(found_product['name'])} – FyboBuybo",
        description=found_product["info"],
        heading=shorten_product_name(found_product["name"]),
        subtitle="A popular UK gift choice",
        products=[found_product],
        related_products=related
        
    )
    
@app.route("/blog")
def blog_index():
    post_list_html = """
    <div style="max-width:900px;margin:60px auto;padding:20px;">
        <h2 style="text-align:center;margin-bottom:40px;font-size:2rem;background:{{ gradient }};-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            Latest Articles
        </h2>
        <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:30px;">
            <div class="card">
                <h3 style="font-size:1.5rem;margin-bottom:10px;">
                    <a href="/blog/8-essential-home-products-to-upgrade-your-space-in-2026" style="color:#bae6fd;text-decoration:none;">
                        8 Essential Home Products to Upgrade Your Space in 2026
                    </a>
                </h3>
                <p style="opacity:.85;font-size:1rem;">Trending Amazon picks to make your space smarter, cozier, and more efficient this year.</p>
            </div>
            <!-- Add more cards here for future posts -->
        </div>
    </div>
    """
    
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    
    rendered = render_template_string(
        BASE_HTML,
        title="Blog – FyboBuybo",
        description="Gift guides, home tips, and trending product recommendations",
        heading="FyboBuybo Blog",
        subtitle="Latest articles on gifts and home inspiration",
        products=[],
        categories=[],  # Empty to skip loop
        css=css,
        canonical_url=SITE_URL + "/blog",
        SITE_URL=SITE_URL,
        slugify=slugify,
        shorten_product_name=shorten_product_name,
        related_products=[],
        gradient=theme["gradient"],
        next_page_url=None,
        prev_page_url=None
    )
    
    # Remove the categories loop entirely (safe replace)
    rendered = rendered.replace('{% for cat in categories %}\n    <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>\n    {% endfor %}', '')
    
    # Insert post list after subtitle
    subtitle_end = rendered.find('</p>', rendered.find('<p class="subtitle">')) + 4
    rendered = rendered[:subtitle_end] + post_list_html + rendered[subtitle_end:]
    
    # Clean empty grids
    rendered = rendered.replace('<div class="grid">\n</div>', '').replace('<div class="grid"></div>', '')
    
    return rendered

@app.route("/blog/<slug>")
def blog_detail(slug):
    post = BLOG_POSTS.get(slug)
    if not post:
        abort(404)
    
    all_products = refresh_products(background=True)
    related = [p for p in all_products if p["category"] in ["Home & Kitchen", "Electronics"]][:6]
    
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    
    rendered = render_template_string(
        BASE_HTML,
        title=post["title"],
        description=post["description"],
        heading=post["heading"],
        subtitle=post["subtitle"],
        products=[],
        categories=[],
        css=css,
        canonical_url=SITE_URL + request.path,
        SITE_URL=SITE_URL,
        slugify=slugify,
        shorten_product_name=shorten_product_name,
        related_products=related,
        gradient=theme["gradient"],
        next_page_url=None,
        prev_page_url=None
    )
    
    rendered = rendered.replace('{% for cat in categories %}\n    <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>\n    {% endfor %}', '')
    
    subtitle_end = rendered.find('</p>', rendered.find('<p class="subtitle">')) + 4
    rendered = rendered[:subtitle_end] + post["content"] + rendered[subtitle_end:]
    
    rendered = rendered.replace('<div class="grid">\n</div>', '').replace('<div class="grid"></div>', '')
    
    return rendered

# ---------------- SEO FILES ---------------- #
@app.route("/robots.txt")
def robots():
    txt = f"""
User-agent: *
Disallow:

Sitemap: {SITE_URL}/sitemap.xml
"""
    return Response(txt, mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    history = load_history()
    urls = {
        (SITE_URL + "/", str(datetime.date.today())),
        (SITE_URL + "/all-gifts", str(datetime.date.today()))
    }

    for day_products in history.values():
        for p in day_products:
            # Category URLs
            urls.add((SITE_URL + "/category/" + slugify(p["category"]), str(datetime.date.today())))
            # Product URLs
            urls.add((SITE_URL + "/product/" + slugify(p["name"]), str(datetime.date.today())))

    sitemap_xml = "<?xml version='1.0' encoding='UTF-8'?>\n"
    sitemap_xml += "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"

    for url, lastmod in sorted(urls):
        sitemap_xml += f"""
  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
  </url>"""

    sitemap_xml += "\n</urlset>"
    return Response(sitemap_xml, mimetype="application/xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
