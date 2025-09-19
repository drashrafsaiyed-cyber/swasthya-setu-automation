import os
import requests
from io import BytesIO
from PIL import Image
from datetime import datetime

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def generate_poster(news_text):
    prompt = f"""
    Create a professional A3 health awareness poster for SWASTHYA SETU CHARITABLE TRUST.

    - Clean vector + modern illustration style.
    - Red and blue medical theme.
    - Big headline encouraging blood donation.
    - Subtext: health awareness + today's date ({datetime.now().strftime("%d %B %Y")}).
    - Include small highlights from today's news: {news_text}.
    - Leave space at the top for the organization's logo.
    """

    url = "https://api.openai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "size": "1024x1536",   # vertical poster format
        "quality": "high"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["data"][0]["b64_json"]

def add_logo(image_b64, logo_path="logo.png"):
    poster = Image.open(BytesIO(base64.b64decode(image_b64))).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    # Resize logo
    logo_width = poster.width // 4
    ratio = logo_width / logo.width
    logo_height = int(logo.height * ratio)
    logo = logo.resize((logo_width, logo_height))

    # Place logo at top center
    pos = ((poster.width - logo_width) // 2, 20)
    poster.paste(logo, pos, logo)

    # Save final
    output_path = "final_poster.png"
    poster.save(output_path)
    return output_path

def send_to_telegram(image_path):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(image_path, "rb") as img_file:
        files = {"photo": img_file}
        data = {"chat_id": TELEGRAM_CHAT_ID}
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()

if __name__ == "__main__":
    try:
        # fetch your news text earlier in the script
        news_text = "Example health + community news headline"
        image_b64 = generate_poster(news_text)
        final_poster = add_logo(image_b64)
        send_to_telegram(final_poster)
        print("✅ Poster generated and sent with logo!")
    except Exception as e:
        print("❌ Error generating/sending poster:", e)
