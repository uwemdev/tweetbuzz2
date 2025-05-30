import tweepy
import hashlib
import time
from datetime import datetime
import json
import asyncio
import subprocess
from pycardano import Network, Address, TransactionBuilder, TransactionOutput, Metadata

# X API credentials
API_KEY = "LxIeablWHgxpCEiDUOf6g2pkG"
API_SECRET = "26lcAEKKxczKF3xUw4Zov0ncnpIcUpGh5ODb0QM1TyRlya0l6J"
ACCESS_TOKEN = "1474009573111607296-p3w5voFz7mdm6sOJM2QGuY3lJUvuac"
ACCESS_TOKEN_SECRET = "iOwVwgKeXz5QMIz41T69GFRpCOU84pdIN0DwF8RmkgLxy"

# Cardano testnet wallet details
WALLET_ADDRESS = "addr_test1qqsg5dt72efhxc96mly92ttvcxwzx2wjnxxpurcccrrn87szcqjeqcrn8u3xdmdrzuyax6r969d5zjm0uxnxacmmlwqs6j3ppt"
NETWORK = Network.TESTNET  # Use testnet for development

# Authenticate with X API
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Function to hash data for integrity
def hash_data(data):
    return hashlib.sha256(data.encode()).hexdigest()

# Function to collect tweets mentioning a keyword
def collect_tweets(keyword, max_tweets=10):
    tweets_data = []
    try:
        for tweet in tweepy.Cursor(api.search_tweets, q=keyword, lang="en", tweet_mode="extended").items(max_tweets):
            try:
                data = {
                    "post_id": tweet.id_str,
                    "timestamp": tweet.created_at.isoformat(),
                    "text": tweet.full_text[:280],  # Truncate to fit metadata limits
                    "likes": tweet.favorite_count,
                    "reposts": tweet.retweet_count,
                    "keyword": keyword,
                    "hash": hash_data(tweet.full_text)
                }
                tweets_data.append(data)
            except AttributeError:
                continue
    except tweepy.TweepError as e:
        print(f"Error fetching tweets: {e}")
        return []
    return tweets_data

# Function to submit data to Cardano testnet as transaction metadata
async def submit_to_blockchain(data):
    # Serialize data for metadata
    data_str = json.dumps(data)
    metadata = Metadata({674: {"tweet_data": data}})  # Metadata label 674 for custom data

    # Prepare transaction data
    tx_data = {
        "network": "testnet",
        "address": WALLET_ADDRESS,
        "amount": 1000000,  # Minimum lovelace (1 ADA)
        "metadata": data
    }

    # Save transaction data to a temporary file
    with open("tx_data.json", "w") as f:
        json.dump(tx_data, f)

    # Call JavaScript helper to sign transaction with Yoroi
    try:
        result = subprocess.run(
            ["node", "sign_transaction.js", "tx_data.json"],
            capture_output=True, text=True, check=True
        )
        tx_id = result.stdout.strip()
        return tx_id
    except subprocess.CalledProcessError as e:
        print(f"Error signing transaction: {e.stderr}")
        return None

# Main function
async def main():
    keyword = "Cardano"
    while True:
        tweets = collect_tweets(keyword, max_tweets=10)
        if not tweets:
            print("No tweets collected, retrying in 60 seconds")
            await asyncio.sleep(60)
            continue
        for tweet_data in tweets:
            tx_id = await submit_to_blockchain(tweet_data)
            if tx_id:
                print(f"Stored tweet {tweet_data['post_id']} with tx_id: {tx_id}")
            else:
                print(f"Failed to store tweet {tweet_data['post_id']}")
        await asyncio.sleep(60)  # Wait 1 minute before next collection

if __name__ == "__main__":
    asyncio.run(main())