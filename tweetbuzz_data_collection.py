import tweepy
import hashlib
import time
from datetime import datetime
import json
import asyncio
import cardano_cli  # Placeholder for Cardano wallet interaction (use pycardano or similar)

# X API credentials (replace with actual keys)
API_KEY = "LxIeablWHgxpCEiDUOf6g2pkG"
API_SECRET = "26lcAEKKxczKF3xUw4Zov0ncnpIcUpGh5ODb0QM1TyRlya0l6J"
ACCESS_TOKEN = "1474009573111607296-p3w5voFz7mdm6sOJM2QGuY3lJUvuac"
ACCESS_TOKEN_SECRET = "iOwVwgKeXz5QMIz41T69GFRpCOU84pdIN0DwF8RmkgLxy"

# Cardano wallet details (replace with actual values)
WALLET_ADDRESS = "your_cardano_wallet_address"
WALLET_KEY = "your_cardano_wallet_key"

# Authenticate with X API
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Function to hash data for integrity
def hash_data(data):
    return hashlib.sha256(data.encode()).hexdigest()

# Function to collect tweets mentioning a keyword
def collect_tweets(keyword, max_tweets=100):
    tweets_data = []
    for tweet in tweepy.Cursor(api.search_tweets, q=keyword, lang="en", tweet_mode="extended").items(max_tweets):
        try:
            data = {
                "post_id": tweet.id_str,
                "timestamp": tweet.created_at.isoformat(),
                "text": tweet.full_text,
                "likes": tweet.favorite_count,
                "reposts": tweet.retweet_count,
                "keyword": keyword,
                "hash": hash_data(tweet.full_text)
            }
            tweets_data.append(data)
        except AttributeError:
            continue
    return tweets_data

# Function to submit data to Cardano blockchain
async def submit_to_blockchain(data):
    # Serialize data
    data_str = json.dumps(data)
    # Placeholder for Cardano transaction (use pycardano or cardano-cli)
    tx = cardano_cli.transaction_build(
        wallet_address=WALLET_ADDRESS,
        wallet_key=WALLET_KEY,
        data=data_str,
        smart_contract_address="tweetbuzz_contract"  # Reference to Plutus contract
    )
    tx_id = cardano_cli.submit_transaction(tx)
    return tx_id

# Main function
async def main():
    keyword = "Cardano"
    while True:
        tweets = collect_tweets(keyword, max_tweets=10)
        for tweet_data in tweets:
            tx_id = await submit_to_blockchain(tweet_data)
            print(f"Stored tweet {tweet_data['post_id']} with tx_id: {tx_id}")
        await asyncio.sleep(60)  # Wait 1 minute before next collection

if __name__ == "__main__":
    asyncio.run(main())