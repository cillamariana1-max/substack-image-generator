import os
import base64
import requests
import feedparser
import re
from pathlib import Path

# ====== CONFIG ======
SUBSTACK_FEED_URL = "https://dannycastonguay1.substack.com/feed"
IMAGES_DIR = Path("images")
IMAGES_DIR.mkdir(exist_ok=True)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Make sure it's configured in GitHub Secrets.")

def slugify(text: str) -> str:
    """
    Very simple slug: lowercase, replace non-letters/numbers with hyphens.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "post"

def generate_prompt(title: str, summary: str | None = None) -> str:
    base = f"Isometric illustration for a tech blog post titled '{title}'. Minimal, clean, modern style, white background."
    if summary:
        base += f" The post is about: {summary[:200]}"
    return base

def generate_image(prompt: str, output_path: Path):
    print(f"Generating image for: {prompt}")

    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-image-1",  # OpenAI image model
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1,
    }

    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    image_b64 = data["data"][0]["b64_json"]
    img_bytes = base64.b64decode(image_b64)

    with open(output_path, "wb") as f:
        f.write(img_bytes)

    print(f"Saved image to {output_path}")

def main():
    def main():
    print(f"Fetching Substack feed from: {SUBSTACK_FEED_URL}")
    feed = feedparser.parse(SUBSTACK_FEED_URL)

    # Substack's RSS is sometimes a bit messy; feedparser sets bozo=True
    # but still gives us usable entries. We just log the warning and continue.
    if feed.bozo:
        print("WARNING: feedparser reported a problem with the feed:")
        print(feed.bozo_exception)

    if not getattr(feed, "entries", None):
        print("No entries found in feed.")
        return

    for entry in feed.entries:
        title = getattr(entry, "title", "Untitled")
        summary = getattr(entry, "summary", None)
        slug = slugify(title)
        output_path = IMAGES_DIR / f"{slug}.png"

        if output_path.exists():
            print(f"Image already exists for '{title}' -> {output_path}, skipping.")
            continue

        prompt = generate_prompt(title, summary)
        generate_image(prompt, output_path)
