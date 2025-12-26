import os
import json
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
import tweepy

TORONTO_TZ = ZoneInfo("America/Toronto")
SLOT = os.getenv("SLOT", "morning").lower()

MORNING_FILE = "promo_morning.json"
EVENING_FILE = "promo_evening.json"
STATE_FILE = "state.json"

# How many recent posts to remember to prevent duplicates
RECENT_LIMIT = 25

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def signature_for(text: str, url: str, slot: str) -> str:
    """
    Create a stable signature that ignores date stamps.
    If content repeats, signature repeats -> we can skip.
    """
    normalized = f"{slot}|{text.strip()}|{url.strip()}|#Bitcoin".lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

# Load schedule
schedule_file = MORNING_FILE if SLOT == "morning" else EVENING_FILE
schedule = load_json(schedule_file)

# Local date/day
now_local = datetime.now(TORONTO_TZ)
day_key = now_local.strftime("%A").lower()
date_key = now_local.strftime("%Y-%m-%d")  # stable date for "already posted today" checks
date_stamp = now_local.strftime("%b %d")   # for the tweet text

item = schedule.get(day_key)
if not item:
    raise ValueError(f"No scheduled post found for {day_key} in {schedule_file}")

# Support dict or string schedule entries
if isinstance(item, dict):
    text = (item.get("text") or "").strip()
    url = (item.get("url") or "").strip()
else:
    text = str(item).strip()
    url = os.getenv("BLOG_URL", "https://easycryptomastery.com/what-is-bitcoin/")

if not text or not url:
    raise ValueError(f"Invalid schedule item for {day_key} in {schedule_file}")

# Load state
state = load_json(STATE_FILE)

# Safety check 1: don't post twice in the same slot on the same day
last_date_for_slot = state.get("last_posted_date", {}).get(SLOT, "")
if last_date_for_slot == date_key:
    print(f"SKIP: Already posted for slot '{SLOT}' on {date_key}.")
    raise SystemExit(0)

# Safety check 2: don't repeat recent content (signature ignores date stamp)
sig = signature_for(text, url, SLOT)
recent = state.get("recent_signatures", [])
if sig in recent:
    print("SKIP: Duplicate detected (recent signature match).")
    raise SystemExit(0)

# Compose tweet (date stamp added, but does not affect duplicate signature)
tweet = f"{text}\n\n{url}\n\n({date_stamp}) #Bitcoin"

# Keep within 280 characters
if len(tweet) > 280:
    overflow = len(tweet) - 280
    text_trimmed = text[:-overflow-3] + "..."
    tweet = f"{text_trimmed}\n\n{url}\n\n({date_stamp}) #Bitcoin"

# Post to X
client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)

client.create_tweet(text=tweet)
print(f"POSTED ({SLOT}): {tweet}")

# Update state and persist
state.setdefault("last_posted_date", {})[SLOT] = date_key
recent.append(sig)
state["recent_signatures"] = recent[-RECENT_LIMIT:]

save_json(STATE_FILE, state)
print("State updated.")
