"""
Generate the synthetic sample dataset for Task 1.3 (wireless-earbuds customer
feedback pipeline): text reviews (JSON), product images (Pillow), a survey
CSV, and short customer-service call audio (Amazon Polly TTS -> real speech,
so Transcribe has genuine audio to work with).

Run once, locally. Writes into data/reviews, data/images, data/surveys,
data/audio. A separate upload step pushes these to S3 raw-data/.
"""
import json
import os
import boto3
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Text reviews
# ---------------------------------------------------------------------------
REVIEWS = [
    # -- good reviews (pass Glue DQ + Lambda validation) --
    {"review_id": "rev-001", "product_id": "WEB-100", "customer_id": "cust-1001",
     "rating": "5", "review_date": "2026-01-14",
     "review_text": "I love these earbuds. The battery lasts all day and the sound quality is excellent for the price. Would definitely recommend to a friend."},
    {"review_id": "rev-002", "product_id": "WEB-100", "customer_id": "cust-1002",
     "rating": "2", "review_date": "2026-01-15",
     "review_text": "The right earbud stopped charging after about two weeks. Sound was good while it worked but this is a terrible reliability issue for a new product."},
    {"review_id": "rev-003", "product_id": "WEB-200-PRO", "customer_id": "cust-1003",
     "rating": "4", "review_date": "2026-01-16",
     "review_text": "Great upgrade over my old pair. Noise cancellation is good, not amazing, but I like the case design a lot."},
    {"review_id": "rev-004", "product_id": "WEB-100", "customer_id": "cust-1004",
     "rating": "1", "review_date": "2026-01-18",
     "review_text": "Package arrived with the case cracked and one earbud missing entirely. Very disappointed with this purchase and the packaging quality."},
    {"review_id": "rev-005", "product_id": "WEB-200-PRO", "customer_id": "cust-1005",
     "rating": "5", "review_date": "2026-01-19",
     "review_text": "Excellent purchase. Comfortable fit, great bass, and the app for customizing the sound profile is a nice touch."},
    {"review_id": "rev-006", "product_id": "WEB-100", "customer_id": "cust-1006",
     "rating": "3", "review_date": "2026-01-20",
     "review_text": "Decent product overall but the touch controls are overly sensitive and I keep pausing my music by accident."},
    {"review_id": "rev-007", "product_id": "WEB-200-PRO", "customer_id": "cust-1007",
     "rating": "2", "review_date": "2026-01-21",
     "review_text": "Bluetooth connection keeps dropping when I walk more than ten feet from my phone. Hoping a firmware update fixes this."},
    {"review_id": "rev-008", "product_id": "WEB-100", "customer_id": "cust-1008",
     "rating": "5", "review_date": "2026-01-22",
     "review_text": "Perfect for the gym. They stay in during workouts and the sweat resistance actually works as advertised."},
    {"review_id": "rev-009", "product_id": "WEB-100", "customer_id": "cust-1009",
     "rating": "1", "review_date": "2026-01-23",
     "review_text": "Product photo showed a black case but I received white. Contacted support and got no response after a week."},
    {"review_id": "rev-010", "product_id": "WEB-200-PRO", "customer_id": "cust-1010",
     "rating": "4", "review_date": "2026-01-24",
     "review_text": "Really good sound for the price point. Only complaint is the charging case is a bit bulky for a jacket pocket."},
    # -- deliberately low-quality reviews (should score low / fail validation) --
    {"review_id": "rev-011", "product_id": "WEB-100", "customer_id": "cust-1011",
     "rating": "5", "review_date": "2026-01-25",
     "review_text": "ok"},
    {"review_id": "rev-012", "product_id": "", "customer_id": "cust-1012",
     "rating": "7", "review_date": "01/26/2026",
     "review_text": "fine i guess"},
]

def write_reviews():
    out_dir = os.path.join(HERE, "reviews")
    for r in REVIEWS:
        path = os.path.join(out_dir, f"{r['review_id']}.json")
        with open(path, "w") as f:
            json.dump(r, f, indent=2)
    print(f"Wrote {len(REVIEWS)} review files to {out_dir}")

# ---------------------------------------------------------------------------
# Survey CSV
# ---------------------------------------------------------------------------
SURVEY_ROWS = [
    ["customer_id", "survey_date", "overall_satisfaction", "product_rating", "service_rating", "improvement_area", "comments"],
    ["cust-2001", "2026-01-15", "5", "5", "4", "None", "Very happy with the earbuds, great value."],
    ["cust-2002", "2026-01-16", "2", "2", "3", "Battery life", "Battery drains much faster than advertised."],
    ["cust-2003", "2026-01-17", "4", "4", "4", "Packaging", "Product good but box was flimsy."],
    ["cust-2004", "2026-01-18", "1", "1", "2", "Build quality", "Earbud stopped pairing after a week."],
    ["cust-2005", "2026-01-19", "5", "5", "5", "None", "Best earbuds I've owned, no complaints."],
    ["cust-2006", "2026-01-20", "3", "3", "3", "Fit and comfort", "A bit uncomfortable after an hour of wear."],
    ["cust-2007", "2026-01-21", "4", "4", "3", "Customer support", "Product is fine, support response was slow."],
    ["cust-2008", "2026-01-22", "2", "2", "2", "Bluetooth connectivity", "Frequent disconnects during calls."],
    ["cust-2009", "2026-01-23", "5", "5", "4", "None", "Sound quality exceeded my expectations."],
    ["cust-2010", "2026-01-24", "3", "4", "2", "Customer support", "Good product but return process was confusing."],
    ["cust-2011", "2026-01-25", "4", "4", "4", "Charging case size", "Solid earbuds, case is a little bulky."],
    ["cust-2012", "2026-01-26", "1", "1", "1", "Build quality", "Right earbud arrived defective, requesting refund."],
]

def write_surveys():
    import csv
    path = os.path.join(HERE, "surveys", "surveys.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(SURVEY_ROWS)
    print(f"Wrote survey CSV to {path} ({len(SURVEY_ROWS) - 1} rows)")

# ---------------------------------------------------------------------------
# Synthetic product images (Pillow) - simple packaging / damage photos with
# baked-in printed text so Textract/Rekognition have something real to find.
# ---------------------------------------------------------------------------
IMAGES = [
    {"file": "WEB-100_packaging.png", "bg": (245, 245, 240), "lines": [
        "TechSound", "Wireless Earbuds WEB-100", "Up to 24hr Battery Life", "IPX5 Sweat Resistant"],
     "shape": ("rect", (60, 260, 340, 380), (30, 30, 30))},
    {"file": "WEB-100_case_damage.png", "bg": (250, 250, 250), "lines": [
        "TechSound WEB-100", "CASE CRACKED ON ARRIVAL"],
     "shape": ("crack", (60, 150, 340, 350), (200, 30, 30))},
    {"file": "WEB-200-PRO_packaging.png", "bg": (20, 20, 25), "lines": [
        "TechSound PRO", "Wireless Earbuds WEB-200-PRO", "Active Noise Cancellation"],
     "shape": ("circle", (150, 220, 250, 320), (240, 240, 240))},
    {"file": "WEB-200-PRO_charging_cable.png", "bg": (240, 240, 240), "lines": [
        "TechSound PRO", "USB-C Charging Cable Included"],
     "shape": ("rect", (100, 260, 300, 280), (10, 10, 10))},
]

def write_images():
    out_dir = os.path.join(HERE, "images")
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except Exception:
        font = ImageFont.load_default()
    for spec in IMAGES:
        img = Image.new("RGB", (400, 400), spec["bg"])
        draw = ImageDraw.Draw(img)
        kind, box, color = spec["shape"]
        if kind == "rect":
            draw.rectangle(box, outline=color, width=4)
        elif kind == "circle":
            draw.ellipse(box, outline=color, width=4)
        elif kind == "crack":
            x0, y0, x1, y1 = box
            draw.rectangle(box, outline=color, width=4)
            draw.line([(x0 + 40, y0), (x0 + 120, (y0 + y1) // 2), (x0 + 60, y1 - 30)], fill=color, width=3)
        text_color = (255, 255, 255) if sum(spec["bg"]) < 400 else (10, 10, 10)
        y = 30
        for line in spec["lines"]:
            draw.text((30, y), line, fill=text_color, font=font)
            y += 32
        img.save(os.path.join(out_dir, spec["file"]))
    print(f"Wrote {len(IMAGES)} images to {out_dir}")

# ---------------------------------------------------------------------------
# Synthetic customer-service call audio (Amazon Polly TTS)
# ---------------------------------------------------------------------------
CALLS = [
    {"file": "call-001_billing_dispute.mp3", "voice": "Joanna", "text": (
        "Thank you for calling Tech Sound support, this is Amanda, how can I help you today? "
        "Hi, I was charged twice for my wireless earbuds order and I would like a refund for the duplicate charge. "
        "I am very sorry about that, let me look up your order right now. "
        "I can see the duplicate charge from January eighteenth, I am processing a refund for that now, it should post within three to five business days. "
        "Thank you, I appreciate you fixing this quickly."
    )},
    {"file": "call-002_defective_product.mp3", "voice": "Matthew", "text": (
        "Hi, thanks for calling support, how can I help? "
        "Yeah hi, my right earbud stopped charging after only two weeks and I am pretty frustrated because these were not cheap. "
        "I completely understand the frustration, that should not happen with a new unit. "
        "I would like a replacement pair sent out please. "
        "Absolutely, I am creating a replacement order right now at no additional cost, you should receive a shipping confirmation within twenty four hours."
    )},
]

def write_audio():
    out_dir = os.path.join(HERE, "audio")
    session = boto3.Session(profile_name="awsgenai", region_name="us-east-1")
    polly = session.client("polly")
    for call in CALLS:
        resp = polly.synthesize_speech(
            Text=call["text"], OutputFormat="mp3", VoiceId=call["voice"], Engine="standard",
        )
        path = os.path.join(out_dir, call["file"])
        with open(path, "wb") as f:
            f.write(resp["AudioStream"].read())
        print(f"Synthesized {path}")

if __name__ == "__main__":
    write_reviews()
    write_surveys()
    write_images()
    write_audio()
