import hashlib
import time
from datetime import datetime
import json
import asyncio
import subprocess
from pycardano import Network, Address, TransactionBuilder, TransactionOutput, Metadata
import snscrape.modules.twitter as sntwitter

# Cardano testnet wallet details
WALLET_ADDRESS = "addr_test1qqsg5dt72efhxc96mly92ttvcxwzx2wjnxxpurcccrrn87szcqjeqcrn8u3xdmdrzuyax6r969d5zjm0uxnxacmmlwqs6j3ppt"
NETWORK = Network.TESTNET  # Use testnet for development

# Mock data for testing
MOCK_TWEETS = [
    {
        "post_id": "mock123",
        "timestamp": datetime.now().isoformat(),
        "text": "Mock tweet about Cardano blockchain!",
        "likes": 5,
        "reposts": 2,
        "keyword": "Cardano",
        "hash": ""
    },
    {
        "post_id": "mock456",
        "timestamp": datetime.now().isoformat(),
        "text": "Cardano is revolutionizing DeFi!",
        "likes": 8,
        "reposts": 3,
        "keyword": "Cardano",
        "hash": ""
    }
]

# Function to hash data for integrity
def hash_data(data):
    return hashlib.sha256(data.encode()).hexdigest()

# Function to collect tweets mentioning a keyword
def collect_tweets(keyword, max_tweets=10, use_mock=True):
    if use_mock:
        print("Using mock tweet data")
        tweets_data = MOCK_TWEETS
        for tweet in tweets_data:
            tweet["timestamp"] = datetime.now().isoformat()  # Update timestamp
            tweet["hash"] = hash_data(tweet["text"])
        return tweets_data

    # Use snscrape to collect tweets without X API
    tweets_data = []
    try:
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(f"{keyword} lang:en").get_items()):
            if i >= max_tweets:
                break
            data = {
                "post_id": str(tweet.id),
                "timestamp": tweet.date.isoformat(),
                "text": tweet.content[:280],  # Truncate to fit metadata limits
                "likes": tweet.likeCount or 0,
                "reposts": tweet.retweetCount or 0,
                "keyword": keyword,
                "hash": hash_data(tweet.content)
            }
            tweets_data.append(data)
    except Exception as e:
        print(f"Error fetching tweets with snscrape: {e}")
        # Fallback to mock data
        tweets_data = MOCK_TWEETS
        for tweet in tweets_data:
            tweet["timestamp"] = datetime.now().isoformat()
            tweet["hash"] = hash_data(tweet["text"])
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
    except FileNotFoundError:
        print("Error: Node.js or sign_transaction.js not found")
        return None

# Main function
async def main():
    keyword = "Cardano"
    use_mock = True  # Set to False to try snscrape
    while True:
        tweets = collect_tweets(keyword, max_tweets=10, use_mock=use_mock)
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