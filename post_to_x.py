import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import tweepy

TORONTO_TZ = ZoneInfo("America/Toronto")

# Which schedule to use: "morning" or "evening"
SLOT = os.getenv("SLOT", "morning").lower()

# Files
MORNING_FILE = "promo_morning.json"
EVENING_FILE = "promo_evening.json"

# X client
client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)

now_local = datetime.now(TORONTO_TZ)
day_key = now_local.strftime("%A").lower()  # monday..sunday
date_stamp = now_local.strftime("%b %d")    # e.g. "Dec 25"

schedule_file = MORNING_FILE if SLOT == "morning" else EVENING_FILE

with open(schedule_file, "r", encoding="utf-8") as f:
    schedule = json.load(f)

item = schedule.get(day_key)
if not item:
    raise ValueError(f"No scheduled post found for {day_key} in {schedule_file}")

# Support either:
# - { "text": "...", "url": "..." }
# - or simple string (legacy)
if isinstance(item, dict):
    text = item.get("text", "").strip()
    url = item.get("url", "").strip()
else:
    text = str(item).strip()
    url = os.getenv("BLOG_URL", "https://easycryptomastery.com/what-is-bitcoin/")

if not text or not url:
    raise ValueError(f"Invalid schedule item for {day_key} in {schedule_file}")

tweet = f"{text}\n\n{url}\n\n({date_stamp}) #Bitcoin"

# Keep within 280
if len(tweet) > 280:
    overflow = len(tweet) - 280
    text_trimmed = text[:-overflow-3] + "..."
    tweet = f"{text_trimmed}\n\n{url}\n\n({date_stamp}) #Bitcoin"

client.create_tweet(text=tweet)
print(f"Posted ({SLOT}): {tweet}")
