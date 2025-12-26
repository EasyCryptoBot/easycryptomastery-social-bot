import os
import json
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
import tweepy

TORONTO_TZ = ZoneInfo("America/Toronto")
SLOT = os.getenv("SLOT", "morning").lower()

FILES = {
    "morning": "promo_morning.json",
    "evening": "promo_evening.json",
    "midday": "engagement_midday.json"
}

STATE_FILE = "state.json"
RECENT_LIMIT = 30

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def signature_for(slot: str, text: str, url: str = "") -> str:
    normalized = f"{slot}|{text.strip()}|{url.strip()}".lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

if SLOT not in FILES:
    raise ValueError(f"Invalid SLOT '{SLOT}'. Use one of: {list(FILES.keys())}")

schedule = load_json(FILES[SLOT])

now_local = datetime.now(TORONTO_TZ)
day_key = now_local.strftime("%A").lower()
date_key = now_local.strftime("%Y-%m-%d")
date_stamp = now_local.strftime("%b %d")

item = schedule.get(day_key)
if not item:
    raise ValueError(f"No scheduled post found for {day_key} in {FILES[SLOT]}")

# Morning/evening: dict preferred (text + url). Midday: string is fine.
text = ""
url = ""

if isinstance(item, dict):
    text = (item.get("text") or "").strip()
    url = (item.get("url") or "").strip()
else:
    text = str(item).strip()

if not text:
    raise ValueError(f"Invalid schedule item for {day_key} in {FILES[SLOT]} (missing text)")

state = load_json(STATE_FILE)
state.setdefault("last_posted_date", {}).setdefault("morning", "")
state["last_posted_date"].setdefault("evening", "")
state["last_posted_date"].setdefault("midday", "")
state.setdefault("recent_signatures", [])

# Safety 1: don't post twice in same slot/day
if state["last_posted_date"][SLOT] == date_key:
    print(f"SKIP: Already posted for slot '{SLOT}' on {date_key}.")
    raise SystemExit(0)

# Safety 2: don't repeat recent content
sig = signature_for(SLOT, text, url)
if sig in state["recent_signatures"]:
    print("SKIP: Duplicate detected (recent signature match).")
    raise SystemExit(0)

# Compose tweet
if SLOT in ("morning", "evening"):
    if not url:
        # fallback if url missing for promo slots
        url = os.getenv("BLOG_URL", "https://easycryptomastery.com/what-is-bitcoin/").strip()
    tweet = f"{text}\n\n{url}\n\n({date_stamp}) #Bitcoin"
else:
    # engagement slot: no link, light hashtag
    tweet = f"{text}\n\n({date_stamp})"

# Fit 280
if len(tweet) > 280:
    overflow = len(tweet) - 280
    text_trimmed = text[:-overflow-3] + "..."
    if SLOT in ("morning", "evening"):
        tweet = f"{text_trimmed}\n\n{url}\n\n({date_stamp}) #Bitcoin"
    else:
        tweet = f"{text_trimmed}\n\n({date_stamp})"

client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)

client.create_tweet(text=tweet)
print(f"POSTED ({SLOT}): {tweet}")

# Update state
state["last_posted_date"][SLOT] = date_key
state["recent_signatures"].append(sig)
state["recent_signatures"] = state["recent_signatures"][-RECENT_LIMIT:]

save_json(STATE_FILE, state)
print("State updated.")
