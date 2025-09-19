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
    - No text repeating the organization name (branding comes only from logo).
    - Poster theme must combine BLOOD DONATION and HEALTH AWARENESS with NEWS CONTEXT.
    - Use these news/health updates from India as 2–3 illustrated icons/captions: {news_text}.
    - Also include at least one general awareness icon (e.g., blood drop, heart, hydration).
    - Modern flat vector style, colourful, infographic-like, attractive for social media.
    """

    url = "https://api.openai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {"model": "gpt-image-1", "prompt": prompt, "size": "1024x1536", "quality": "high"}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["data"][0]["b64_json"]


def add_logo(image_b64, logo_path="logo.png"):
    """Overlay logo at top-right corner, larger size"""
    poster = Image.open(BytesIO(base64.b64decode(image_b64))).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    # Resize logo (1/4 poster width)
    logo_width = poster.width // 4
    ratio = logo_width / logo.width
    logo_height = int(logo.height * ratio)
    logo = logo.resize((logo_width, logo_height))

    # Paste at top-right corner with small margin
    pos = (poster.width - logo_width - 30, 30)
    poster.paste(logo, pos, logo)

    output_path = "final_poster.png"
    poster.save(output_path)
    return output_path
