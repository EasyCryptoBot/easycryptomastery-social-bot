import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import tweepy

# ===== SETTINGS =====
TORONTO_TZ = ZoneInfo("America/Toronto")

# Change this if your slug is different
BLOG_URL = os.getenv("BLOG_URL", "https://easycryptomastery.com/what-is-bitcoin/")

SCHEDULE_FILE = "promo_week_what_is_bitcoin.json"

# ===== X CLIENT (OAuth 1.0a user context) =====
client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)

# ===== PICK TODAY'S MESSAGE (Toronto local day) =====
now_local = datetime.now(TORONTO_TZ)
day_key = now_local.strftime("%A").lower()  # monday, tuesday, etc.
date_stamp = now_local.strftime("%b %d")    # e.g., "Dec 25"

with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
    schedule = json.load(f)

base_text = schedule.get(day_key)
if not base_text:
    raise ValueError(f"No scheduled tweet found for day: {day_key}")

# Add a small date stamp to prevent X blocking repeats across weeks
tweet = f"{base_text}\n\n{BLOG_URL}\n\n({date_stamp}) #Bitcoin"

# Safety: keep within X limit
if len(tweet) > 280:
    # Trim the base text if needed (rare, but safe)
    overflow = len(tweet) - 280
    base_text_trimmed = base_text[:-overflow-3] + "..."
    tweet = f"{base_text_trimmed}\n\n{BLOG_URL}\n\n({date_stamp}) #Bitcoin"

client.create_tweet(text=tweet)
print("Tweet posted:", tweet)
