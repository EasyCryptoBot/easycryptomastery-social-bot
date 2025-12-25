import os
import tweepy

client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)

tweet = "TEST POST 🚀 EasyCryptoMastery automation is now live."

client.create_tweet(text=tweet)
print("Tweet posted successfully")
