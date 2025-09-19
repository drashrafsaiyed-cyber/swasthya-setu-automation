import os
import requests
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime

# 🔑 Load secrets from GitHub Actions
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ✅ Awareness fallback tips
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
    """Generate poster image using OpenAI Images API and return local file path"""
    if not news_text or len(news_text.strip()) < 10:
        news_text = ", ".join(AWARENESS_TIPS[:3])

    prompt = f"""
    Create a modern, professional A3 health awareness poster for SWASTHYA SETU CHARITABLE TRUST.

    - Style: clean, vibrant, modern, infographic-like
    - Theme: blood donation & health awareness
    - Use colorful vector graphics and engaging visuals
    - Add today's date: {datetime.now().strftime('%d %B %Y')}
    - Include these updates: {news_text}
    - Leave blank space at the bottom-right corner for the official logo
    """

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    data = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "size": "1024x1536",
        "quality": "high"
    }

    response = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=data)
    response.raise_for_status()
    result = response.json()

    if "data" not in result or "url" not in result["data"][0]:
        raise ValueError("Unexpected OpenAI response: " + str(result))

    # Download the generated image
    img_url = result["data"][0]["url"]
    img_response = requests.get(img_url)
    img_response.raise_for_status()

    image = Image.open(BytesIO(img_response.content)).convert("RGBA")

    # ✅ Overlay the logo
    if os.path.exists("logo.png"):
        try:
            logo = Image.open("logo.png").convert("RGBA")
            # Resize logo to ~15% of poster width
            logo_width = image.width // 6
            ratio = logo_width / logo.width
            logo_height = int(logo.height * ratio)
            logo = logo.resize((logo_width, logo_height))

            # Position: bottom-right corner with margin
            position = (image.width - logo_width - 30, image.height - logo_height - 30)
            image.paste(logo, position, logo)
        except Exception as e:
            print("⚠️ Could not add logo:", e)

    # Save final poster
    output_path = "final_poster.png"
    image.save(output_path, "PNG")
    return output_path

def send_to_telegram(image_path, news_text):
    """Send the poster to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(image_path, "rb") as img:
            files = {"photo": img}
            caption = (
                f"🩸 Swasthya Setu Charitable Trust\n\n"
                f"📅 {datetime.now().strftime('%d %B %Y')}\n\n"
                f"📰 {news_text}\n\n"
                "#DonateBlood #HealthAwareness"
            )
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
