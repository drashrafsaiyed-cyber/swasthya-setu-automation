import os
import requests
from datetime import datetime

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def fetch_health_news():
    """Grab a few fresh health headlines (local/national/international mix)."""
    if not NEWS_API_KEY:
        return "Blood donation saves lives. Community health updates daily."
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "category": "health",
        "language": "en",
        "pageSize": 3,
        "apiKey": NEWS_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        headlines = [a["title"] for a in data.get("articles", []) if a.get("title")]
        return " • ".join(headlines)[:500] or "Health news highlights."
    except Exception as e:
        print("News error:", e)
        return "Health news highlights."

def generate_poster(news_text):
    """Create an A3-style poster image (square render for Telegram) with your branding."""
    prompt = f"""
    Design a clean, modern A3 poster for **SWASTHYA SETU CHARITABLE TRUST**.
    Theme: Blood Donation Awareness + Community Health Awareness.
    Elements: bold red & white palette, medical icons, inclusive community vibes, no heavy text blocks.
    Include today's date: {datetime.now().strftime("%d %B %Y")}.
    Include short, tasteful ticker-style headlines (no logos of news orgs): {news_text}.
    Prominent headline idea: "Donate Blood. Save Lives."
    Subline: "Regular donation builds a healthier community."
    Place the organization name clearly near the top. Avoid tiny text. No phone numbers unless provided.
    Avoid using any third-party brand logos or copyrighted marks. No gore.
    """
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "size": "1024x1024"
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["data"][0]["url"]

def send_to_telegram(image_url, caption):
    """Send generated image to your Telegram chat/channel."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": image_url,
        "caption": caption
    }
    r = requests.post(url, data=payload, timeout=60)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    headlines = fetch_health_news()
    img_url = generate_poster(headlines)
    caption = "🩸 Daily Blood Donation & Community Health Poster — SWASTHYA SETU CHARITABLE TRUST"
    send_to_telegram(img_url, caption)
    print("Done.")
