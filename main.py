import os
import base64
import requests
from io import BytesIO
from PIL import Image, ImageOps
from datetime import datetime

# 🔑 Secrets from GitHub
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ✅ Fallback awareness tips
AWARENESS_TIPS = [
    "Stay hydrated during hot weather",
    "Eat fresh fruits and vegetables daily",
    "Regular exercise keeps your heart healthy",
    "Mental health matters – take breaks",
    "Preventive checkups save lives"
]

def fetch_latest_news():
    """Fetch top 3 health headlines from NewsAPI"""
    if not NEWS_API_KEY:
        return None
    url = f"https://newsapi.org/v2/top-headlines?category=health&language=en&pageSize=5&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        if not articles:
            return None
        headlines = [a["title"] for a in articles[:3] if "title" in a]
        return ", ".join(headlines)
    except Exception as e:
        print("❌ Error fetching news:", e)
        return None

def generate_poster(news_text):
    """Generate poster using OpenAI Images API"""
    if not news_text or len(news_text.strip()) < 10:
        news_text = ", ".join(AWARENESS_TIPS[:3])

    prompt = f"""
    Design a modern, vibrant A3 health awareness poster for SWASTHYA SETU CHARITABLE TRUST.

    Layout:
    - Leave the top blank for the official logo (do not generate any logo or text).
    - Big bold headline in bright colour (red/orange/blue).
    - Subtext: short health awareness message.
    - Lower half: include 3–4 illustrated icons with captions.
    - At least 2 captions MUST come from these news/health updates: {news_text}.
    - Remaining captions should come from health awareness tips.
    - Modern vector style, colourful gradients, engaging background, infographic-like.
    """

    url = "https://api.openai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {"model": "gpt-image-1", "prompt": prompt, "size": "1024x1536", "quality": "high"}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["data"][0]["b64_json"]

def add_logo(image_b64, logo_path="logo.png"):
    """Overlay logo at clean position above poster content"""
    poster = Image.open(BytesIO(base64.b64decode(image_b64))).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    # Resize logo (1/5 width of poster)
    logo_width = poster.width // 5
    ratio = logo_width / logo.width
    logo_height = int(logo.height * ratio)
    logo = logo.resize((logo_width, logo_height))

    # Add white padding at TOP so logo sits above poster
    padding_top = logo_height + 40
    poster_with_border = ImageOps.expand(poster, border=(0, padding_top, 0, 0), fill="white")

    # Paste logo at top center (inside white margin, not overlapping text)
    pos = ((poster_with_border.width - logo_width) // 2, 20)
    poster_with_border.paste(logo, pos, logo)

    output_path = "final_poster.png"
    poster_with_border.save(output_path)
    return output_path

def send_to_telegram(image_path, news_text):
    """Send final poster to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    caption = (
        f"🩸 Swasthya Setu Charitable Trust\n\n"
        f"📰 Latest Health Updates:\n"
        + "\n".join([f"• {line.strip()}" for line in news_text.split(',')])
        + "\n\n#DonateBlood #HealthAwareness"
    )
    with open(image_path, "rb") as img_file:
        files = {"photo": img_file}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()

if __name__ == "__main__":
    try:
        news_text = fetch_latest_news()
        image_b64 = generate_poster(news_text)
        final_poster = add_logo(image_b64)
        send_to_telegram(final_poster, news_text if news_text else ", ".join(AWARENESS_TIPS[:3]))
        print("✅ Poster generated and sent with logo + news!")
    except Exception as e:
        print("❌ Error generating/sending poster:", e)
