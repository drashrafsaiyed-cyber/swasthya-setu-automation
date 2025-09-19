import os
import requests
import base64
from datetime import datetime

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def fetch_health_news():
    """Fetch top health headlines (fallback if API not available)."""
    if not NEWS_API_KEY:
        return "Donate blood, save lives. Stay healthy together."
    url = "https://newsapi.org/v2/top-headlines"
    params = {"category": "health", "language": "en", "pageSize": 3, "apiKey": NEWS_API_KEY}
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        headlines = [a["title"] for a in data.get("articles", []) if a.get("title")]
        return " • ".join(headlines)[:500]
    except Exception as e:
        print("News error:", e)
        return "Health news updates unavailable today."

def generate_poster(news_text):
    """Generate a poster image and return URL or base64 upload."""
    prompt = f"""
    Design a bold, modern A3 poster for SWASTHYA SETU CHARITABLE TRUST.
    Theme: Blood Donation Awareness + Community Health Awareness.
    Include today's date: {datetime.now().strftime("%d %B %Y")}.
    Add short health headlines: {news_text}.
    Style: clean, medical theme, strong red & white colors.
    """

    url = "https://api.openai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "gpt-image-1", "prompt": prompt, "size": "1024x1024"}

    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()

    # If URL is available
    if "url" in data["data"][0]:
        return data["data"][0]["url"]

    # If base64 is returned
    if "b64_json" in data["data"][0]:
        img_data = base64.b64decode(data["data"][0]["b64_json"])
        # Upload to Telegram as a file (since no URL)
        files = {"photo": ("poster.png", img_data)}
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "caption": "🩸 Daily Poster — SWASTHYA SETU CHARITABLE TRUST"}
        r = requests.post(tg_url, data=payload, files=files, timeout=60)
        r.raise_for_status()
        print("Poster sent via base64 upload ✅")
        return None

    raise ValueError("No image returned from OpenAI")

def send_to_telegram(image_url, caption):
    """Send poster via URL (if available)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "photo": image_url, "caption": caption}
    r = requests.post(url, data=payload, timeout=60)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    news = fetch_health_news()
    try:
        img_url = generate_poster(news)
        if img_url:  # if URL-based
            caption = f"🩸 Daily Blood Donation & Health Awareness Poster\nSWASTHYA SETU CHARITABLE TRUST\n\n📰 {news}"
            send_to_telegram(img_url, caption)
        print("Poster workflow complete ✅")
    except Exception as e:
        print("Error generating/sending poster:", e)
