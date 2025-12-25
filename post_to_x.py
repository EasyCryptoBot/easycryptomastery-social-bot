import os
from datetime import datetime, timezone
import tweepy

client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
tweet = f"✅ EasyCryptoMastery bot check-in: automation is live ({now}). #Bitcoin"

client.create_tweet(text=tweet)
print("Tweet posted successfully")
