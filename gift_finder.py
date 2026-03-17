"""
gift_finder.py — FyboBuybo Gift Finder
======================================
Add this file to your project root and register the blueprint (or inline the routes)
in app.py. See integration instructions at the bottom.

MATCHING LOGIC (easy to maintain):
====================================
Each product in PRODUCTS can have a "tags" dict like:
    {
      "recipient": ["her", "friend", "partner"],
      "interests": ["beauty", "home"],
      "occasion":  ["birthday", "christmas", "justbecause"]
    }

The scorer awards points per matching tag and returns the top 4–6 products.
To add a new product to the quiz pool, just add/update its tags dict.
You don't touch the quiz or scoring logic at all.

INTEGRATION INTO app.py:
=========================
1. Place this file next to app.py
2. Add near the top of app.py:
       from gift_finder import gift_finder_bp
       app.register_blueprint(gift_finder_bp)
3. That's it — /gift-finder and /gift-finder/results are now live.

NAV + CTA HOOKS (manual additions to BASE_HTML in app.py):
===========================================================
a) In the nav <nav class="nav-links"> block, add after the blog link:
       <a href="/gift-finder">Gift Finder</a>

b) On the homepage hero, add a third action button:
       <a href="/gift-finder" class="btn-ghost">Find the perfect gift →</a>

c) On every category/seasonal page, add before the product grid:
       <div style="text-align:center;margin:24px 0 8px">
         <a href="/gift-finder" style="color:var(--slate);font-size:.88rem;font-weight:600;
            border-bottom:1px solid var(--slate-line)">
           Not sure what to buy? Try our Gift Finder →
         </a>
       </div>
"""

import re
import json
import random
from flask import Blueprint, request, render_template_string, abort
from products_data import PRODUCTS

gift_finder_bp = Blueprint("gift_finder", __name__)

# ─────────────────────────────────────────────────────────────────────────────
# TAG DEFINITIONS
# These map quiz answers to internal tag strings.
# If you add a new quiz option, just add its tag here.
# ─────────────────────────────────────────────────────────────────────────────

RECIPIENT_TAGS = {
    "her":      ["her", "friend", "partner"],
    "him":      ["him", "friend", "partner"],
    "child":    ["child"],
    "parent":   ["parent", "her", "him"],
    "friend":   ["friend", "her", "him"],
    "teacher":  ["teacher", "friend"],
    "partner":  ["partner", "her", "him"],
}

INTEREST_TAGS = {
    "beauty":   ["beauty"],
    "home":     ["home"],
    "books":    ["books"],
    "tech":     ["tech"],
    "sports":   ["sports"],
    "arts":     ["arts"],
    "food":     ["food"],
    "fashion":  ["fashion"],
    "pets":     ["pets"],
    "outdoors": ["outdoors"],
    "health":   ["health"],
}

OCCASION_TAGS = {
    "birthday":    ["birthday"],
    "christmas":   ["christmas"],
    "mothersday":  ["mothersday"],
    "fathersday":  ["fathersday"],
    "valentines":  ["valentines"],
    "easter":      ["easter"],
    "justbecause": ["justbecause"],
    "newbaby":     ["newbaby"],
    "thankyou":    ["thankyou"],
}

# ─────────────────────────────────────────────────────────────────────────────
# PRODUCT TAG MAP
# Maps product ASINs (or slugified names) to tag sets.
# Add any product from PRODUCTS here to include it in quiz results.
# Format:
#   "ASIN_OR_NAME_KEY": {
#       "recipient": [...],   # who it suits
#       "interests": [...],   # interest tags
#       "occasion":  [...],   # occasion tags
#       "why": "One-line reason why this gift works"
#   }
# ─────────────────────────────────────────────────────────────────────────────

PRODUCT_TAGS: dict = {
    # ── The tag map is built dynamically from product categories and seasons ──
    # ── so you rarely need to edit this manually. See auto_tag() below. ──────
    # ── You CAN add manual overrides here for specific ASINs: ────────────────
    # "B09EXAMPLE": {
    #     "recipient": ["her", "partner"],
    #     "interests": ["beauty"],
    #     "occasion":  ["birthday", "valentines"],
    #     "why":       "A luxurious treat she wouldn't buy for herself"
    # },
}


def auto_tag(product: dict) -> dict:
    """
    Automatically derive recipient/interest/occasion tags from a product's
    category and season fields. This means every product in PRODUCTS is
    quiz-eligible without manual tagging — the richer the product data,
    the better the matching.
    Manual overrides in PRODUCT_TAGS take precedence.
    """
    if product.get("gift_finder_tags"):
        return product["gift_finder_tags"]
    asin = product.get("asin", "")
    if asin and asin in PRODUCT_TAGS:
        return PRODUCT_TAGS[asin]

    cat = (product.get("category") or "").lower()
    season = (product.get("season") or "").lower()
    keywords = " ".join(product.get("keywords") or []).lower()
    name = (product.get("name") or "").lower()
    text = f"{cat} {season} {keywords} {name}"

    # ── Recipient ────────────────────────────────────────────────────
    recipient = []
    if any(w in text for w in ["women", "woman", "her", "lady", "ladies", "feminine", "girls", "mum", "mam", "moms"]):
        recipient += ["her"]
    if any(w in text for w in ["men", "man", "him", "dad", "boys", "gents", "gentleman"]):
        recipient += ["him"]
    if any(w in text for w in ["child", "kids", "baby", "toddler", "infant", "nursery", "toy", "game"]):
        recipient += ["child"]
    if any(w in text for w in ["mum", "mom", "dad", "parent", "father", "mother"]):
        recipient += ["parent"]
    if "teacher" in text:
        recipient += ["teacher"]
    if any(w in text for w in ["couple", "partner", "love", "romantic", "valentine"]):
        recipient += ["partner"]
    # Default: most products suit friends/general giving
    if not recipient:
        recipient = ["friend", "her", "him"]
    recipient = list(set(recipient))

    # ── Interests ────────────────────────────────────────────────────
    interests = []
    if any(w in text for w in ["beauty", "skincare", "cosmetic", "fragrance", "perfume", "makeup", "grooming", "spa"]):
        interests += ["beauty"]
    if any(w in text for w in ["home", "kitchen", "cooking", "baking", "storage", "candle", "decor", "bedding", "cleaning", "organisation"]):
        interests += ["home"]
    if any(w in text for w in ["book", "read", "learning", "education", "journal", "stationary", "stationery"]):
        interests += ["books"]
    if any(w in text for w in ["tech", "electronic", "gadget", "device", "smart", "digital", "camera", "headphone", "speaker"]):
        interests += ["tech"]
    if any(w in text for w in ["sport", "fitness", "exercise", "yoga", "gym", "running", "cycling", "swim"]):
        interests += ["sports"]
    if any(w in text for w in ["art", "craft", "creative", "paint", "draw", "knit", "sew", "puzzle"]):
        interests += ["arts"]
    if any(w in text for w in ["food", "drink", "coffee", "tea", "wine", "chocolate", "gourmet", "snack", "bbq", "bake"]):
        interests += ["food"]
    if any(w in text for w in ["fashion", "clothing", "apparel", "wear", "bag", "wallet", "jewellery", "jewelry", "accessory"]):
        interests += ["fashion"]
    if any(w in text for w in ["pet", "dog", "cat", "animal"]):
        interests += ["pets"]
    if any(w in text for w in ["outdoor", "travel", "camping", "garden", "hiking", "adventure"]):
        interests += ["outdoors"]
    if not interests:
        interests = ["home"]  # safe default

    # ── Occasion ─────────────────────────────────────────────────────
    occasion = ["birthday", "christmas", "justbecause"]  # always safe defaults
    if any(w in text for w in ["valentine", "romantic", "love"]):
        occasion += ["valentines"]
    if any(w in text for w in ["mother", "mum", "mom"]):
        occasion += ["mothersday"]
    if any(w in text for w in ["father", "dad"]):
        occasion += ["fathersday"]
    if "easter" in text:
        occasion += ["easter"]
    if any(w in text for w in ["baby", "newborn", "infant", "nursery"]):
        occasion += ["newbaby"]
    if any(w in text for w in ["thank", "appreciation"]):
        occasion += ["thankyou"]
    occasion = list(set(occasion))

    # ── Why one-liner ─────────────────────────────────────────────────
    why_map = {
        "beauty": "A genuinely indulgent pick she'll use every day",
        "home":   "A thoughtful upgrade for their home they'd never buy themselves",
        "tech":   "A well-reviewed gadget that'll get used every single day",
        "sports": "Perfect for someone who takes their fitness seriously",
        "food":   "A treat they'll actually enjoy — not just look at",
        "fashion":"A considered style pick they can wear immediately",
        "pets":   "For the pet lover who spoils their animals (rightly so)",
        "books":  "For the reader who always has a 'to-read' list",
        "arts":   "A creative gift that encourages their favourite hobby",
        "outdoors":"For anyone who loves getting outside — whatever the British weather",
    }
    why = next((why_map[i] for i in interests if i in why_map), "A top-rated UK pick they'll genuinely appreciate")

    return {
        "recipient": recipient,
        "interests": interests,
        "occasion": occasion,
        "why": why,
    }


def score_product(product: dict, recipient: str, interests: list, occasion: str) -> int:
    """
    Score a product against the quiz answers.
    Higher = better match. Returns 0 if it fundamentally doesn't fit.

    Scoring weights (easy to tune):
      Recipient match:  +40  (most important — wrong recipient = bad gift)
      Interest match:   +25 per interest matched
      Occasion match:   +15
    """
    tags = auto_tag(product)

    score = 0

    # Expand the quiz answer through the tag lookup tables
    r_tags  = set(RECIPIENT_TAGS.get(recipient, [recipient]))
    i_tags  = set()
    for interest in interests:
        i_tags.update(INTEREST_TAGS.get(interest, [interest]))
    o_tags  = set(OCCASION_TAGS.get(occasion, [occasion]))

    # Recipient — hard gating: no match = zero score
    product_recipients = set(tags.get("recipient", []))
    if not r_tags.intersection(product_recipients):
        return 0
    score += 40

    # Interests — additive; more matches = higher score
    product_interests = set(tags.get("interests", []))
    matched_interests = i_tags.intersection(product_interests)
    score += len(matched_interests) * 25

    # Occasion
    product_occasions = set(tags.get("occasion", []))
    if o_tags.intersection(product_occasions):
        score += 15

    # Boost products with good ratings
    try:
        rating = float(product.get("manual_rating") or 0)
        if rating >= 4.5:
            score += 8
        elif rating >= 4.0:
            score += 4
    except (ValueError, TypeError):
        pass

    return score


def get_recommendations(recipient: str, interests: list, occasion: str, limit: int = 6) -> list:
    """
    Returns top `limit` products for the given quiz answers.
    Falls back to category-broadening if fewer than 4 results are found.
    """
    scored = []
    for p in PRODUCTS:
        s = score_product(p, recipient, interests, occasion)
        if s > 0:
            tags = auto_tag(p)
            scored.append((s, p, tags.get("why", "")))

    scored.sort(key=lambda x: x[0], reverse=True)

    # If we have a good pool, take top results with slight randomisation
    # to avoid showing the exact same 4 products every time
    top_pool = scored[:max(limit * 3, 12)]
    if len(top_pool) >= limit:
        # Take guaranteed top 2, then random from next pool for variety
        guaranteed = top_pool[:2]
        rest = top_pool[2:]
        random.shuffle(rest)
        selected = guaranteed + rest[:limit - 2]
    else:
        selected = top_pool[:limit]

    # Fallback: if still fewer than 4, relax recipient constraint
    if len(selected) < 4:
        fallback = []
        for p in PRODUCTS:
            tags = auto_tag(p)
            i_tags = set()
            for interest in interests:
                i_tags.update(INTEREST_TAGS.get(interest, [interest]))
            product_interests = set(tags.get("interests", []))
            if i_tags.intersection(product_interests) and p not in [x[1] for x in selected]:
                fallback.append((15, p, tags.get("why", "")))
        fallback.sort(key=lambda x: x[0], reverse=True)
        selected += fallback[:limit - len(selected)]

    return [(p, why) for _, p, why in selected[:limit]]


# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'&', '-and-', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


# ─────────────────────────────────────────────────────────────────────────────
# QUIZ TEMPLATE
# ─────────────────────────────────────────────────────────────────────────────

QUIZ_TEMPLATE = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gift Finder – FyboBuybo</title>
<meta name="description" content="Answer 3 quick questions and discover the perfect gift — handpicked from top-rated Amazon UK products.">
<link rel="canonical" href="https://www.fybobuybo.com/gift-finder">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,400;1,600&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet">

<style>
/* ── Reset & base ─────────────────────────────────────────── */
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  font-family:'DM Sans',sans-serif;
  background:#f0ece4;
  color:#1a1a18;
  min-height:100vh;
  overflow-x:hidden;
  -webkit-font-smoothing:antialiased;
}

/* ── CSS variables ───────────────────────────────────────── */
:root{
  --ink:#1a1a18;
  --ink-2:#3d3c38;
  --muted:#7a7870;
  --bg:#f0ece4;
  --bg-2:#e8e3d8;
  --card:#faf8f4;
  --navy:#0e1f40;
  --cta:#c84b0e;
  --cta-hover:#a33a08;
  --green:#1a7a50;
  --border:rgba(26,26,24,0.10);
  --border-2:rgba(26,26,24,0.18);
  --sh-sm:0 2px 12px rgba(26,26,24,0.07),0 6px 24px rgba(26,26,24,0.06);
  --sh-md:0 6px 32px rgba(26,26,24,0.10),0 16px 56px rgba(26,26,24,0.10);
  --sh-lg:0 12px 56px rgba(26,26,24,0.14),0 32px 80px rgba(26,26,24,0.14);
  --r:14px;
  --r-lg:22px;
  --r-pill:99px;
  --ease:cubic-bezier(0.16,1,0.3,1);
}

/* ── Page wrapper ────────────────────────────────────────── */
.gf-page{
  min-height:100vh;
  display:flex;
  flex-direction:column;
  position:relative;
}

/* ── Decorative background blobs ────────────────────────── */
.gf-blob{
  position:fixed;
  border-radius:50%;
  filter:blur(80px);
  pointer-events:none;
  z-index:0;
  opacity:.45;
}
.blob-1{width:500px;height:500px;background:rgba(200,75,14,.12);top:-100px;right:-100px;}
.blob-2{width:400px;height:400px;background:rgba(14,31,64,.08);bottom:-80px;left:-80px;}
.blob-3{width:300px;height:300px;background:rgba(26,122,80,.07);top:40%;left:30%;}

/* ── Nav bar ─────────────────────────────────────────────── */
.gf-nav{
  position:sticky;top:0;z-index:100;
  background:rgba(240,236,228,.92);
  backdrop-filter:blur(20px) saturate(160%);
  border-bottom:1px solid var(--border);
  padding:0 32px;
}
.gf-nav-inner{
  max-width:820px;margin:0 auto;
  display:flex;align-items:center;
  justify-content:space-between;
  height:58px;
}
.gf-logo{
  font-family:'Cormorant Garamond',serif;
  font-size:1.45rem;font-weight:600;
  letter-spacing:-.03em;
  color:var(--navy);
  text-decoration:none;
  display:flex;align-items:baseline;gap:1px;
}
.gf-logo em{color:var(--cta);font-style:italic}
.gf-back{
  font-size:.8rem;font-weight:500;
  color:var(--muted);
  text-decoration:none;
  display:flex;align-items:center;gap:6px;
  padding:6px 14px;border-radius:var(--r-pill);
  border:1px solid var(--border);
  background:rgba(255,255,255,.55);
  transition:all .2s;
}
.gf-back:hover{color:var(--navy);border-color:var(--border-2);background:rgba(255,255,255,.85);}
.gf-back svg{width:12px;height:12px;stroke:currentColor;fill:none;stroke-width:2;}

/* ── Main container ──────────────────────────────────────── */
.gf-main{
  flex:1;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:flex-start;
  padding:48px 24px 80px;
  position:relative;z-index:1;
}

/* ── Progress bar ────────────────────────────────────────── */
.progress-wrap{
  width:100%;max-width:520px;
  margin-bottom:40px;
}
.progress-meta{
  display:flex;align-items:center;
  justify-content:space-between;
  margin-bottom:10px;
}
.progress-label{
  font-size:.72rem;font-weight:600;
  letter-spacing:.16em;text-transform:uppercase;
  color:var(--muted);
}
.progress-step{
  font-family:'Cormorant Garamond',serif;
  font-size:.95rem;font-weight:600;
  color:var(--navy);
  letter-spacing:-.01em;
}
.progress-track{
  height:3px;border-radius:2px;
  background:var(--border);overflow:hidden;
}
.progress-fill{
  height:100%;
  background:linear-gradient(90deg,var(--cta),#e8701a);
  border-radius:2px;
  transition:width .55s var(--ease);
}

/* ── Quiz card ───────────────────────────────────────────── */
.quiz-card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:var(--r-lg);
  padding:44px 48px 40px;
  max-width:560px;width:100%;
  box-shadow:var(--sh-md);
  position:relative;
  overflow:hidden;
}
.quiz-card::before{
  content:'';position:absolute;
  inset:0;border-radius:var(--r-lg);
  background:linear-gradient(135deg,rgba(255,255,255,.6) 0%,transparent 100%);
  pointer-events:none;
}

/* Step transition animations */
.quiz-card{transition:opacity .3s ease,transform .3s var(--ease);}
.quiz-card.fade-out{opacity:0;transform:translateX(-18px);}
.quiz-card.fade-in{animation:fadeIn .38s var(--ease) both;}
@keyframes fadeIn{from{opacity:0;transform:translateX(18px)}to{opacity:1;transform:translateX(0)}}

.quiz-eyebrow{
  font-size:.68rem;font-weight:700;
  letter-spacing:.2em;text-transform:uppercase;
  color:var(--cta);margin-bottom:14px;
  display:flex;align-items:center;gap:9px;
}
.quiz-eyebrow::before{
  content:'';display:block;width:16px;height:1px;background:var(--cta);
}
.quiz-q{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(1.7rem,4vw,2.2rem);
  font-weight:600;line-height:1.12;
  letter-spacing:-.04em;color:var(--ink);
  margin-bottom:8px;
}
.quiz-sub{
  font-size:.87rem;color:var(--muted);
  font-weight:300;margin-bottom:30px;
  line-height:1.6;
}

/* ── Option grid ─────────────────────────────────────────── */
.opt-grid{
  display:grid;
  gap:10px;
  margin-bottom:28px;
}
.opt-grid.col-2{grid-template-columns:1fr 1fr;}
.opt-grid.col-1{grid-template-columns:1fr;}

.opt-btn{
  display:flex;align-items:center;gap:12px;
  padding:14px 18px;
  border:1.5px solid var(--border-2);
  border-radius:var(--r);
  background:rgba(255,255,255,.65);
  font-family:'DM Sans',sans-serif;
  font-size:.9rem;font-weight:500;
  color:var(--ink-2);
  cursor:pointer;
  transition:all .2s var(--ease);
  text-align:left;
  position:relative;
  overflow:hidden;
}
.opt-btn::after{
  content:'';position:absolute;inset:0;
  background:var(--cta);opacity:0;
  transition:opacity .2s;
  pointer-events:none;
}
.opt-btn:hover{
  border-color:var(--cta);
  color:var(--navy);
  transform:translateY(-2px);
  box-shadow:var(--sh-sm);
  background:rgba(255,255,255,.95);
}
.opt-btn.selected{
  border-color:var(--cta);
  background:rgba(200,75,14,.07);
  color:var(--navy);
  font-weight:600;
  box-shadow:0 0 0 3px rgba(200,75,14,.12);
}
.opt-btn.selected .opt-check{
  background:var(--cta);
  border-color:var(--cta);
  color:#fff;
}
.opt-icon{
  font-size:1.25rem;line-height:1;
  flex-shrink:0;width:28px;text-align:center;
}
.opt-label{flex:1;}
.opt-check{
  width:20px;height:20px;border-radius:50%;
  border:1.5px solid var(--border-2);
  background:rgba(255,255,255,.7);
  display:flex;align-items:center;justify-content:center;
  flex-shrink:0;
  transition:all .2s;
  font-size:.65rem;
}

/* ── CTA button ──────────────────────────────────────────── */
.quiz-cta{
  display:flex;align-items:center;justify-content:center;
  gap:10px;width:100%;
  padding:15px 24px;
  background:var(--navy);
  color:#fff;
  border:none;border-radius:var(--r-pill);
  font-family:'DM Sans',sans-serif;
  font-size:.95rem;font-weight:600;
  letter-spacing:-.01em;
  cursor:pointer;
  transition:all .22s var(--ease);
  box-shadow:0 4px 18px rgba(14,31,64,.28),0 2px 6px rgba(14,31,64,.18);
}
.quiz-cta:hover{
  background:var(--cta);
  transform:translateY(-2px);
  box-shadow:0 8px 28px rgba(200,75,14,.35),0 4px 10px rgba(200,75,14,.2);
}
.quiz-cta:disabled{
  opacity:.4;cursor:not-allowed;
  transform:none!important;
  box-shadow:none!important;
}
.quiz-cta svg{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2.2;}

/* ── Results page ────────────────────────────────────────── */
.results-header{
  max-width:820px;width:100%;
  text-align:center;margin-bottom:40px;
}
.results-eyebrow{
  font-size:.68rem;font-weight:700;
  letter-spacing:.2em;text-transform:uppercase;
  color:var(--cta);margin-bottom:16px;
  display:flex;align-items:center;justify-content:center;gap:10px;
}
.results-eyebrow::before,.results-eyebrow::after{
  content:'';display:block;width:24px;height:1px;background:var(--cta);
}
.results-title{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(2rem,5vw,3.2rem);
  font-weight:600;line-height:1.08;
  letter-spacing:-.05em;color:var(--ink);
  margin-bottom:14px;
}
.results-title em{font-style:italic;color:var(--navy);}
.results-sub{
  font-size:1rem;color:var(--muted);
  font-weight:300;max-width:500px;margin:0 auto;
  line-height:1.72;
}

/* ── Results grid ────────────────────────────────────────── */
.results-grid{
  max-width:900px;width:100%;
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
  gap:20px;
  margin-bottom:48px;
}

.res-card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:var(--r-lg);
  overflow:hidden;
  display:flex;flex-direction:column;
  box-shadow:var(--sh-sm);
  transition:transform .3s var(--ease),box-shadow .3s ease;
  animation:cardIn .5s var(--ease) both;
}
.res-card:hover{
  transform:translateY(-6px);
  box-shadow:var(--sh-lg);
}
@keyframes cardIn{
  from{opacity:0;transform:translateY(20px)}
  to{opacity:1;transform:translateY(0)}
}

.res-img{
  aspect-ratio:1;background:#edeae3;overflow:hidden;
  display:flex;align-items:center;justify-content:center;
}
.res-img img{
  width:100%;height:100%;
  object-fit:contain;padding:20px;
  transition:transform .5s ease;
}
.res-card:hover .res-img img{transform:scale(1.06);}

.res-body{padding:20px;display:flex;flex-direction:column;flex:1;gap:10px;}
.res-cat{
  font-size:.67rem;font-weight:700;
  letter-spacing:.14em;text-transform:uppercase;color:var(--cta);
}
.res-name{
  font-family:'Cormorant Garamond',serif;
  font-size:1.05rem;font-weight:600;
  line-height:1.3;letter-spacing:-.02em;color:var(--ink);
}
.res-why{
  font-size:.82rem;line-height:1.6;
  color:var(--muted);font-weight:300;
  background:rgba(200,75,14,.05);
  border-left:2px solid var(--cta);
  padding:8px 12px;border-radius:0 6px 6px 0;
  flex:1;font-style:italic;
}
.res-cta-row{display:flex;flex-direction:column;gap:7px;margin-top:4px;}
.res-amz{
  display:flex;align-items:center;justify-content:center;gap:8px;
  padding:11px 16px;
  background:var(--cta);color:#fff;
  border-radius:var(--r-pill);
  font-size:.845rem;font-weight:600;
  text-decoration:none;
  transition:background .2s,transform .2s,box-shadow .2s;
  box-shadow:0 4px 14px rgba(200,75,14,.28);
  letter-spacing:-.01em;
}
.res-amz:hover{
  background:var(--cta-hover);
  transform:translateY(-1px);
  box-shadow:0 8px 22px rgba(200,75,14,.36);
}
.res-amz em{font-style:italic;font-size:1em;font-weight:700;}
.res-detail{
  display:block;text-align:center;
  font-size:.78rem;font-weight:500;color:var(--muted);
  padding:7px;border:1px solid var(--border);border-radius:var(--r);
  text-decoration:none;transition:all .2s;
}
.res-detail:hover{color:var(--navy);border-color:rgba(14,31,64,.2);background:rgba(14,31,64,.04);}

/* ── Results actions ─────────────────────────────────────── */
.results-actions{
  max-width:560px;width:100%;
  text-align:center;
}
.retake-btn{
  display:inline-flex;align-items:center;gap:9px;
  padding:14px 28px;
  border:1.5px solid var(--border-2);
  border-radius:var(--r-pill);
  background:rgba(255,255,255,.7);
  font-family:'DM Sans',sans-serif;
  font-size:.9rem;font-weight:600;color:var(--ink-2);
  cursor:pointer;text-decoration:none;
  transition:all .22s;
  margin-bottom:14px;
}
.retake-btn:hover{
  background:#fff;border-color:var(--navy);
  color:var(--navy);
  box-shadow:var(--sh-sm);transform:translateY(-1px);
}
.retake-btn svg{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;}
.browse-link{
  display:block;margin-top:10px;
  font-size:.88rem;color:var(--muted);font-weight:400;
  text-decoration:none;
  transition:color .2s;
}
.browse-link:hover{color:var(--navy);}

/* ── Share bar ───────────────────────────────────────────── */
.share-bar{
  max-width:560px;width:100%;
  display:flex;align-items:center;gap:10px;
  justify-content:center;
  margin:32px 0 0;flex-wrap:wrap;
}
.share-label{
  font-size:.76rem;font-weight:600;
  letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);
}
.share-btn{
  display:inline-flex;align-items:center;gap:7px;
  padding:9px 18px;border-radius:var(--r-pill);
  font-family:'DM Sans',sans-serif;
  font-size:.8rem;font-weight:600;
  text-decoration:none;cursor:pointer;border:none;
  transition:all .2s;
}
.share-wa{background:#25D366;color:#fff;}
.share-wa:hover{background:#1ebe59;transform:translateY(-1px);}
.share-fb{background:#1877F2;color:#fff;}
.share-fb:hover{background:#0d6ae0;transform:translateY(-1px);}
.share-em{background:var(--bg-2);color:var(--ink-2);border:1px solid var(--border-2);}
.share-em:hover{background:#fff;transform:translateY(-1px);color:var(--navy);}
.share-btn svg{width:14px;height:14px;fill:currentColor;}

/* ── Affil note ──────────────────────────────────────────── */
.affil-note{
  max-width:560px;width:100%;
  margin-top:32px;
  padding:12px 18px;
  border:1px solid var(--border);border-radius:var(--r);
  background:rgba(255,255,255,.5);
  font-size:.76rem;line-height:1.6;color:var(--muted);
  text-align:center;
}
.affil-note a{color:#4a7aaa;font-weight:500;}

/* ── Footer ──────────────────────────────────────────────── */
.gf-footer{
  padding:24px;text-align:center;
  font-size:.76rem;color:var(--muted);
  border-top:1px solid var(--border);
  position:relative;z-index:1;
}
.gf-footer a{color:var(--muted);text-decoration:underline;}

/* ── Mobile ──────────────────────────────────────────────── */
@media(max-width:600px){
  .quiz-card{padding:32px 24px 28px;}
  .opt-grid.col-2{grid-template-columns:1fr;}
  .gf-main{padding:32px 16px 64px;}
  .results-grid{grid-template-columns:1fr;}
}
</style>
</head>

<body>
<!-- Background blobs -->
<div class="gf-blob blob-1" aria-hidden="true"></div>
<div class="gf-blob blob-2" aria-hidden="true"></div>
<div class="gf-blob blob-3" aria-hidden="true"></div>

<!-- Nav -->
<header class="gf-nav">
  <div class="gf-nav-inner">
    <a href="/" class="gf-logo">Fybo<em>Buybo</em></a>
    <a href="/" class="gf-back">
      <svg viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"/></svg>
      Back to site
    </a>
  </div>
</header>

<!-- Main -->
<main class="gf-main" id="gf-main" role="main">

  <!-- ═══ QUIZ UI (shown by JS) ═══════════════════════════════════════════ -->
  <div id="quiz-wrap" style="width:100%;display:flex;flex-direction:column;align-items:center;">

    <!-- Progress -->
    <div class="progress-wrap" id="progress-wrap">
      <div class="progress-meta">
        <span class="progress-label" id="progress-label">Step 1 of 3</span>
        <span class="progress-step" id="progress-step">Who are you buying for?</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" id="progress-fill" style="width:33%"></div>
      </div>
    </div>

    <!-- Step 1: Recipient -->
    <div class="quiz-card" id="step-1" role="group" aria-labelledby="q1-title">
      <div class="quiz-eyebrow">Step 1 of 3</div>
      <h1 class="quiz-q" id="q1-title">Who are you buying for?</h1>
      <p class="quiz-sub">Pick the person closest to who you have in mind.</p>
      <div class="opt-grid col-2" role="radiogroup" aria-label="Recipient">
        <button class="opt-btn" data-value="her" data-step="1" aria-pressed="false">
          <span class="opt-icon">👩</span>
          <span class="opt-label">Her</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="him" data-step="1" aria-pressed="false">
          <span class="opt-icon">👨</span>
          <span class="opt-label">Him</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="child" data-step="1" aria-pressed="false">
          <span class="opt-icon">🧒</span>
          <span class="opt-label">Child</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="parent" data-step="1" aria-pressed="false">
          <span class="opt-icon">👴</span>
          <span class="opt-label">Parent</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="friend" data-step="1" aria-pressed="false">
          <span class="opt-icon">🤝</span>
          <span class="opt-label">Friend</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="teacher" data-step="1" aria-pressed="false">
          <span class="opt-icon">📚</span>
          <span class="opt-label">Teacher</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="partner" data-step="1" aria-pressed="false">
          <span class="opt-icon">💑</span>
          <span class="opt-label">Partner</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
      </div>
      <button class="quiz-cta" id="step1-next" disabled aria-label="Continue to interests">
        Continue
        <svg viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </button>
    </div>

    <!-- Step 2: Interests (multi-select, hidden initially) -->
    <div class="quiz-card" id="step-2" style="display:none" role="group" aria-labelledby="q2-title">
      <div class="quiz-eyebrow">Step 2 of 3</div>
      <h2 class="quiz-q" id="q2-title">What are their interests?</h2>
      <p class="quiz-sub">Pick up to 3 — the more you choose, the better the match.</p>
      <div class="opt-grid col-2" role="group" aria-label="Interests (select up to 3)">
        <button class="opt-btn" data-value="beauty" data-step="2" data-multi="true" aria-pressed="false">
          <span class="opt-icon">✨</span>
          <span class="opt-label">Beauty & Skincare</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="home" data-step="2" data-multi="true" aria-pressed="false">
          <span class="opt-icon">🏠</span>
          <span class="opt-label">Home & Kitchen</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="books" data-step="2" data-multi="true" aria-pressed="false">
          <span class="opt-icon">📖</span>
          <span class="opt-label">Books & Learning</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="tech" data-step="2" data-multi="true" aria-pressed="false">
          <span class="opt-icon">⚡</span>
          <span class="opt-label">Tech & Gadgets</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="sports" data-step="2" data-multi="true" aria-pressed="false">
          <span class="opt-icon">🏃</span>
          <span class="opt-label">Sports & Fitness</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="arts" data-step="2" data-multi="true" aria-pressed="false">
          <span class="opt-icon">🎨</span>
          <span class="opt-label">Arts & Crafts</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="food" data-step="2" data-multi="true" aria-pressed="false">
          <span class="opt-icon">☕</span>
          <span class="opt-label">Food & Drink</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="fashion" data-step="2" data-multi="true" aria-pressed="false">
          <span class="opt-icon">👗</span>
          <span class="opt-label">Fashion</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="pets" data-step="2" data-multi="true" aria-pressed="false">
          <span class="opt-icon">🐾</span>
          <span class="opt-label">Pets</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="outdoors" data-step="2" data-multi="true" aria-pressed="false">
          <span class="opt-icon">🌿</span>
          <span class="opt-label">Outdoors & Travel</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="health" data-step="2" data-multi="true" aria-pressed="false">
          <span class="opt-icon">🌿</span>
          <span class="opt-label">Health & Wellness</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
      </div>
      <button class="quiz-cta" id="step2-next" disabled aria-label="Continue to occasion">
        Continue
        <svg viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </button>
    </div>

    <!-- Step 3: Occasion (hidden initially) -->
    <div class="quiz-card" id="step-3" style="display:none" role="group" aria-labelledby="q3-title">
      <div class="quiz-eyebrow">Step 3 of 3</div>
      <h2 class="quiz-q" id="q3-title">What's the occasion?</h2>
      <p class="quiz-sub">This helps us tailor the picks to the moment.</p>
      <div class="opt-grid col-2" role="radiogroup" aria-label="Occasion">
        <button class="opt-btn" data-value="birthday" data-step="3" aria-pressed="false">
          <span class="opt-icon">🎂</span>
          <span class="opt-label">Birthday</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="christmas" data-step="3" aria-pressed="false">
          <span class="opt-icon">🎄</span>
          <span class="opt-label">Christmas</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="mothersday" data-step="3" aria-pressed="false">
          <span class="opt-icon">💐</span>
          <span class="opt-label">Mother's Day</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="fathersday" data-step="3" aria-pressed="false">
          <span class="opt-icon">👔</span>
          <span class="opt-label">Father's Day</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="valentines" data-step="3" aria-pressed="false">
          <span class="opt-icon">❤️</span>
          <span class="opt-label">Valentine's Day</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="easter" data-step="3" aria-pressed="false">
          <span class="opt-icon">🐣</span>
          <span class="opt-label">Easter</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="justbecause" data-step="3" aria-pressed="false">
          <span class="opt-icon">🎁</span>
          <span class="opt-label">Just Because</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="newbaby" data-step="3" aria-pressed="false">
          <span class="opt-icon">👶</span>
          <span class="opt-label">New Baby</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
        <button class="opt-btn" data-value="thankyou" data-step="3" aria-pressed="false">
          <span class="opt-icon">🙏</span>
          <span class="opt-label">Thank You</span>
          <span class="opt-check" aria-hidden="true">✓</span>
        </button>
      </div>
      <button class="quiz-cta" id="step3-submit" disabled aria-label="Find my gifts">
        Find my gifts ✦
        <svg viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </button>
    </div>

  </div><!-- /#quiz-wrap -->

  <!-- ═══ RESULTS (server-rendered, shown only on /gift-finder/results) ═══ -->
  {% if results is defined %}
  <div id="results-wrap" style="width:100%;display:flex;flex-direction:column;align-items:center;">

    <div class="results-header">
      <div class="results-eyebrow">Your personalised picks</div>
      <h1 class="results-title">We found <em>{{ results|length }} great gifts</em></h1>
      <p class="results-sub">
        Handpicked for <strong>{{ recipient_label }}</strong> who loves <strong>{{ interests_label }}</strong>
        — perfect for <strong>{{ occasion_label }}</strong>.
      </p>
    </div>

    <div class="results-grid" role="list">
      {% for product, why in results %}
      <article class="res-card" style="animation-delay:{{ loop.index0 * 0.08 }}s" role="listitem">
        <div class="res-img">
          <img src="{{ product.image }}" alt="{{ product.name }}" loading="lazy" width="300" height="300">
        </div>
        <div class="res-body">
          <div class="res-cat">{{ product.category }}</div>
          <div class="res-name">{{ product.name[:80] }}{% if product.name|length > 80 %}…{% endif %}</div>
          <div class="res-why">{{ why }}</div>
          <div class="res-cta-row">
            {% if product.url %}
            <a href="{{ product.url }}" target="_blank" rel="nofollow sponsored noopener" class="res-amz">
              Check price on <em>amazon</em>
            </a>
            {% endif %}
            <a href="/product/{{ slugify(product.name) }}" class="res-detail">Full details →</a>
          </div>
        </div>
      </article>
      {% endfor %}
    </div>

    <!-- Retake + browse -->
    <div class="results-actions">
      <div style="margin-bottom:16px">
        <span style="font-size:.82rem;color:var(--muted);font-weight:300">
          Not quite right? Adjust your answers or browse everything.
        </span>
      </div>
      <a href="/gift-finder" class="retake-btn">
        <svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
        Retake the quiz
      </a>
      <a href="/" class="browse-link">Browse all gifts →</a>
    </div>

    <!-- Share bar -->
    {% set share_url = "https://www.fybobuybo.com/gift-finder/results?" + query_string %}
    {% set share_text = "I found the perfect gift on FyboBuybo — check it out!" %}
    <div class="share-bar" aria-label="Share your results">
      <span class="share-label">Share</span>
      <a href="https://wa.me/?text={{ (share_text + ' ' + share_url)|urlencode }}"
         target="_blank" rel="noopener" class="share-btn share-wa" aria-label="Share on WhatsApp">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/>
        </svg>
        WhatsApp
      </a>
      <a href="https://www.facebook.com/sharer/sharer.php?u={{ share_url|urlencode }}"
         target="_blank" rel="noopener" class="share-btn share-fb" aria-label="Share on Facebook">
        <svg viewBox="0 0 24 24"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>
        Facebook
      </a>
      <a href="mailto:?subject=Found%20a%20great%20gift%20idea&body={{ (share_text + ' ' + share_url)|urlencode }}"
         class="share-btn share-em" aria-label="Share via email">
        <svg viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
        Email
      </a>
    </div>

    <!-- Affil note -->
    <p class="affil-note">
      FyboBuybo earns a small commission when you buy through our links — at no extra cost to you.
      <a href="/privacy-policy">Learn more</a>
    </p>

  </div><!-- /#results-wrap -->
  {% endif %}

</main>

<footer class="gf-footer">
  <a href="/privacy-policy">Privacy Policy</a> ·
  <a href="/terms">Terms</a> ·
  © 2026 FyboBuybo
</footer>

<script>
// ════════════════════════════════════════════════════════════════
// GIFT FINDER — Vanilla JS Quiz Engine
// ════════════════════════════════════════════════════════════════

(function () {
  "use strict";

  // Quiz state
  const state = {
    recipient:  null,     // single string
    interests:  [],       // array, max 3
    occasion:   null,     // single string
    currentStep: 1,
  };

  const MAX_INTERESTS = 3;

  // ── Element refs ─────────────────────────────────────────────
  const steps       = [null, el("step-1"), el("step-2"), el("step-3")];
  const step1Next   = el("step1-next");
  const step2Next   = el("step2-next");
  const step3Submit = el("step3-submit");
  const progressFill  = el("progress-fill");
  const progressLabel = el("progress-label");
  const progressStep  = el("progress-step");

  // On results page: hide quiz entirely
  const resultsWrap = document.getElementById("results-wrap");
  const quizWrap    = document.getElementById("quiz-wrap");
  if (resultsWrap) {
    quizWrap.style.display = "none";
    return; // nothing else to do
  }

  // ── Helper ───────────────────────────────────────────────────
  function el(id) { return document.getElementById(id); }

  // ── Step 1: Single-select ────────────────────────────────────
  steps[1].querySelectorAll(".opt-btn[data-step='1']").forEach(function (btn) {
    btn.addEventListener("click", function () {
      steps[1].querySelectorAll(".opt-btn[data-step='1']").forEach(function (b) {
        b.classList.remove("selected");
        b.setAttribute("aria-pressed", "false");
      });
      btn.classList.add("selected");
      btn.setAttribute("aria-pressed", "true");
      state.recipient = btn.dataset.value;
      step1Next.disabled = false;
    });
  });

  step1Next.addEventListener("click", function () { goToStep(2); });

  // ── Step 2: Multi-select (max 3) ─────────────────────────────
  steps[2].querySelectorAll(".opt-btn[data-step='2']").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const val     = btn.dataset.value;
      const isSelected = btn.classList.contains("selected");

      if (isSelected) {
        btn.classList.remove("selected");
        btn.setAttribute("aria-pressed", "false");
        state.interests = state.interests.filter(function (v) { return v !== val; });
      } else {
        if (state.interests.length >= MAX_INTERESTS) {
          // Deselect oldest selection
          const oldest = state.interests.shift();
          const oldBtn = steps[2].querySelector('.opt-btn[data-value="' + oldest + '"]');
          if (oldBtn) {
            oldBtn.classList.remove("selected");
            oldBtn.setAttribute("aria-pressed", "false");
          }
        }
        btn.classList.add("selected");
        btn.setAttribute("aria-pressed", "true");
        state.interests.push(val);
      }
      step2Next.disabled = state.interests.length === 0;
    });
  });

  step2Next.addEventListener("click", function () { goToStep(3); });

  // ── Step 3: Single-select ─────────────────────────────────────
  steps[3].querySelectorAll(".opt-btn[data-step='3']").forEach(function (btn) {
    btn.addEventListener("click", function () {
      steps[3].querySelectorAll(".opt-btn[data-step='3']").forEach(function (b) {
        b.classList.remove("selected");
        b.setAttribute("aria-pressed", "false");
      });
      btn.classList.add("selected");
      btn.setAttribute("aria-pressed", "true");
      state.occasion = btn.dataset.value;
      step3Submit.disabled = false;
    });
  });

  step3Submit.addEventListener("click", function () { submitQuiz(); });

  // ── Navigation ────────────────────────────────────────────────
  function goToStep(targetStep) {
    const current = steps[state.currentStep];
    current.classList.add("fade-out");

    setTimeout(function () {
      current.style.display = "none";
      current.classList.remove("fade-out");

      const next = steps[targetStep];
      next.style.display = "block";
      next.classList.add("fade-in");
      next.removeEventListener("animationend", cleanFade);
      next.addEventListener("animationend", cleanFade, { once: true });

      state.currentStep = targetStep;
      updateProgress(targetStep);

      // Scroll to top of quiz on step change
      quizWrap.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 280);
  }

  function cleanFade(e) { e.target.classList.remove("fade-in"); }

  // ── Progress bar ──────────────────────────────────────────────
  const stepLabels = ["", "Who are you buying for?", "What are their interests?", "What's the occasion?"];
  function updateProgress(step) {
    const pct = Math.round((step / 3) * 100);
    progressFill.style.width = pct + "%";
    progressLabel.textContent = "Step " + step + " of 3";
    progressStep.textContent  = stepLabels[step];
  }

  // ── Submit → redirect to results ─────────────────────────────
  function submitQuiz() {
    if (!state.recipient || state.interests.length === 0 || !state.occasion) return;

    const params = new URLSearchParams();
    params.set("r", state.recipient);
    params.set("i", state.interests.join(","));
    params.set("o", state.occasion);

    // Show a brief loading state on the button
    step3Submit.textContent = "Finding your gifts…";
    step3Submit.disabled = true;

    window.location.href = "/gift-finder/results?" + params.toString();
  }

})();
</script>

</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────────
# HUMAN-READABLE LABELS (used in results page summary)
# ─────────────────────────────────────────────────────────────────────────────

RECIPIENT_LABELS = {
    "her": "her", "him": "him", "child": "a child", "parent": "a parent",
    "friend": "a friend", "teacher": "a teacher", "partner": "your partner",
}
INTEREST_LABELS = {
    "beauty": "Beauty & Skincare", "home": "Home & Kitchen", "books": "Books & Learning",
    "tech": "Tech & Gadgets", "sports": "Sports & Fitness", "arts": "Arts & Crafts",
    "food": "Food & Drink", "fashion": "Fashion", "pets": "Pets", "outdoors": "Outdoors & Travel",
}
OCCASION_LABELS = {
    "birthday": "a birthday", "christmas": "Christmas", "mothersday": "Mother's Day",
    "fathersday": "Father's Day", "valentines": "Valentine's Day", "easter": "Easter",
    "justbecause": "just because", "newbaby": "a new baby", "thankyou": "a thank you",
}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@gift_finder_bp.route("/gift-finder")
def gift_finder():
    return render_template_string(QUIZ_TEMPLATE)


@gift_finder_bp.route("/gift-finder/results")
def gift_finder_results():
    recipient = request.args.get("r", "").strip().lower()
    interests_raw = request.args.get("i", "").strip().lower()
    occasion = request.args.get("o", "").strip().lower()

    # Validate
    valid_recipients = set(RECIPIENT_TAGS.keys())
    valid_interests  = set(INTEREST_TAGS.keys())
    valid_occasions  = set(OCCASION_TAGS.keys())

    if recipient not in valid_recipients:
        return render_template_string(QUIZ_TEMPLATE), 200

    interests = [i for i in interests_raw.split(",") if i in valid_interests][:3]
    if not interests:
        interests = ["home"]

    if occasion not in valid_occasions:
        occasion = "justbecause"

    results = get_recommendations(recipient, interests, occasion, limit=6)

    recipient_label  = RECIPIENT_LABELS.get(recipient, recipient)
    interests_label  = " & ".join(INTEREST_LABELS.get(i, i) for i in interests)
    occasion_label   = OCCASION_LABELS.get(occasion, occasion)

    query_string = f"r={recipient}&i={','.join(interests)}&o={occasion}"

    return render_template_string(
        QUIZ_TEMPLATE,
        results=results,
        slugify=slugify,
        recipient_label=recipient_label,
        interests_label=interests_label,
        occasion_label=occasion_label,
        query_string=query_string,
    )
