import os
import base64
import requests
from io import BytesIO
from PIL import Image
from datetime import datetime

# 🔑 Load secrets from GitHub Actions (from repository secrets)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ✅ Fallback awareness tips if NewsAPI fails
AWARENESS_TIPS = [
    "Drink water regularly to stay hydrated.",
    "Eat a balanced diet with fruits and vegetables.",
    "Get at least 30 minutes of physical activity daily.",
    "Donate blood — it saves lives.",
    "Avoid smoking and excessive alcohol consumption.",
    "Wash your hands to prevent infections.",
]

def fetch_news():
    """Fetch latest health/community news using NewsAPI"""
    url = f"https://newsapi.org/v2/top-headlines?country=in&category=health&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        if not articles:
            return ", ".join(AWARENESS_TIPS[:3])
        top_headlines = [a["title"] for a in articles[:3] if "title" in a]
        return " • ".join(top_headlines)
    except Exception as e:
        print("Error fetching news:", e)
        return ", ".join(AWARENESS_TIPS[:3])

def generate_poster(news_text):
    """Generate poster image using OpenAI Images API"""
    prompt = f"""
    Create a modern, professional A3 health awareness poster for SWASTHYA SETU CHARITABLE TRUST.

    - Style: clean, vibrant, modern, infographic-style
    - Theme: blood donation & health awareness
    - Use colorful vector graphics and engaging visuals
    - Add today's date: {datetime.now().strftime('%d %B %Y')}
    - Include these updates: {news_text}
    """

    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        data = {
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": "1024x1536",  # portrait / A3 aspect
            "quality": "high",
            "response_format": "b64_json"
        }

        response = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=data)
        response.raise_for_status()
        image_base64 = response.json()["data"][0]["b64_json"]

        image_bytes = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_bytes))

        # ✅ Add the logo at bottom-right corner
        if os.path.exists("logo.png"):
            logo = Image.open("logo.png").convert("RGBA")
            logo = logo.resize((150, 150))  # adjust size
            position = (image.width - logo.width - 30, image.height - logo.height - 30)
            image.paste(logo, position, logo)

        output_path = "poster.png"
        image.save(output_path)
        return output_path
    except Exception as e:
        print("Error generating poster:", e)
        return None

def send_to_telegram(image_path, news_text):
    """Send the poster to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(image_path, "rb") as img:
            files = {"photo": img}
            caption = f"🩸 Swasthya Setu Charitable Trust\n\n📅 {datetime.now().strftime('%d %B %Y')}\n\n📰 {news_text}\n\n#DonateBlood #HealthAwareness"
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
            response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        print("✅ Poster sent to Telegram successfully!")
    except Exception as e:
        print("Error sending to Telegram:", e)

if __name__ == "__main__":
    headlines = fetch_news()
    poster_path = generate_poster(headlines)
    if poster_path:
        send_to_telegram(poster_path, headlines)
