import os
import base64
import requests
from io import BytesIO
from PIL import Image
from datetime import datetime

# 🔑 Secrets from GitHub
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ✅ Awareness tips (fallback if news is weak)
AWARENESS_TIPS = [
    "Stay hydrated during hot weather",
    "Eat fresh fruits and vegetables daily",
    "Regular exercise keeps your heart healthy",
    "Mental health matters – take breaks",
    "Preventive checkups save lives"
]


def fetch_latest_news():
    """Fetch top 3 India health headlines from NewsAPI"""
    if not NEWS_API_KEY:
        return None
    url = f"https://newsapi.org/v2/top-headlines?country=in&category=health&pageSize=5&apiKey={NEWS_API_KEY}"
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
    Design a modern, vibrant A3 awareness poster for SWASTHYA SETU CHARITABLE TRUST.

    Layout:
    - Top-right corner reserved for official logo (do not recreate the logo).
    - Big bold headline in engaging colours (red/orange/blue/green).
    - Do NOT repeat the organization name in text (logo handles branding).
    - Theme must COMBINE blood donation + health awareness + current news context.
    - Use these India health news updates as 2–3 illustrated icons/captions: {news_text}.
    - Add at least one general awareness icon (blood drop, heart, hydration, doctor).
    - Use modern flat vector style, colourful gradients, infographic feel, social-media ready.
    """

    url = "https://api.openai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "size": "1024x1536",  # Portrait, A3-like
        "quality": "high"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["data"][0]["b64_json"]


def add_logo(image_b64, logo_path="logo.png"):
    """Overlay logo at top-right corner, larger size"""
    poster = Image.open(BytesIO(base64.b64decode(image_b64))).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    # Resize logo (about 1/4 poster width → fairly large)
    logo_width = poster.width // 4
    ratio = logo_width / logo.width
    logo_height = int(logo.height * ratio)
    logo = logo.resize((logo_width, logo_height))

    # Paste at top-right with margin
    pos = (poster.width - logo_width - 40, 40)
    poster.paste(logo, pos, logo)

    output_path = "final_poster.png"
    poster.save(output_path)
    return output_path


def send_to_telegram(image_path):
    """Send final poster to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(image_path, "rb") as img_file:
        files = {"photo": img_file}
        data = {"chat_id": TELEGRAM_CHAT_ID}
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()


if __name__ == "__main__":
    try:
        print("🚀 Starting automation...")

        # ✅ Fetch latest India health news
        news_text = fetch_latest_news()
        print("📰 News fetched:", news_text)

        # ✅ Generate poster
        image_b64 = generate_poster(news_text)
        print("🎨 Poster generated")

        # ✅ Add logo
        final_poster = add_logo(image_b64)
        print("✅ Logo added:", final_poster)

        # ✅ Send to Telegram
        send_to_telegram(final_poster)
        print("📩 Poster sent to Telegram!")

    except Exception as e:
        import traceback
        print("❌ Error generating/sending poster:", e)
        traceback.print_exc()

        # Fallback Telegram alert
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": f"🚨 Poster automation failed: {str(e)}"
            }
            requests.post(url, data=data)
            print("⚠️ Sent failure alert to Telegram")
        except Exception as tel_err:
            print("❌ Could not send failure alert to Telegram:", tel_err)
