from flask import Flask, render_template_string, Response

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ForYourBuysOnly UK</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">
  <style>
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
  </style>
</head>
<body>
  <h1>ForYourBuysOnly</h1>
  <p class="subtitle">Top UK trending buys · Updated daily</p>
  
  <div class="grid">
    <div class="card">
      <div class="tag">Drinks</div>
      <h2>Guinness Draught Nitrosurge</h2>
      <p>Get ready to experience the ultimate game-changer in beer with Guinness Draught Nitrosurge, a revolutionary drink that will take your tastebuds on a wild ride! With its unparalleled smoothness and iconic Guinness flavor.</p>
      <button>Grab It Now 🔥</button>
    </div>

    <div class="card">
      <div class="tag">Household</div>
      <h2>Velvet Toilet Tissue 24 Rolls</h2>
      <p>Experience the softest wipe of your life with Velvet Toilet Tissue 24 Rolls! This 24-roll pack is the must-have essential for unbeatable comfort and value.</p>
      <button>Grab It Now 🔥</button>
    </div>

    <div class="card">
      <div class="tag">Health</div>
      <h2>Nutrition Geeks Magnesium Glycinate</h2>
      <p>Unlock deeper sleep, boosted energy, and enhanced wellness with Nutrition Geeks Magnesium Glycinate, trusted by thousands across the UK.</p>
      <button>Grab It Now 🔥</button>
    </div>

    <div class="card">
      <div class="tag">Games</div>
      <h2>Herd Mentality Board Game</h2>
      <p>Unleash your competitive spirit with Herd Mentality Board Game, the ultimate UK sensation that will challenge your friendships and strategic thinking!</p>
      <button>Grab It Now 🔥</button>
    </div>

    <div class="card">
      <div class="tag">Home Comfort</div>
      <h2>Electric Heated Blanket</h2>
      <p>Experience cozy nights like never before with the Electric Heated Blanket — a warm hug for your entire body, perfect for winter evenings.</p>
      <button>Grab It Now 🔥</button>
    </div>

    <div class="card">
      <div class="tag">Books</div>
      <h2>Diary of a Wimpy Kid: Partypooper</h2>
      <p>Laugh out loud with the most epic installment yet — 'Diary of a Wimpy Kid: Partypooper' promises hilarious chaos and relatable fun for all ages.</p>
      <button>Grab It Now 🔥</button>
    </div>

    <div class="card">
      <div class="tag">Books</div>
      <h2>Murdle Puzzle Book</h2>
      <p>Challenge your brain with the UK's most addictive puzzle book! Murdle Puzzle Book tests your problem-solving skills with uniquely crafted puzzles.</p>
      <button>Grab It Now 🔥</button>
    </div>

    <div class="card">
      <div class="tag">Tech</div>
      <h2>INIU Portable Charger</h2>
      <p>Keep your devices powered on-the-go with the INIU Portable Charger — reliable, compact, and essential for busy lifestyles.</p>
      <button>Grab It Now 🔥</button>
    </div>
  </div>

  <footer>
    Affiliate links may earn commission · Made with AI <br>
    No tracking · No cookies · Just top UK finds
  </footer>
</body>
</html>
"""

@app.route("/")
def home():
    return Response(render_template_string(HTML), mimetype="text/html")

if __name__ == "__main__":
    app.run(debug=True)
