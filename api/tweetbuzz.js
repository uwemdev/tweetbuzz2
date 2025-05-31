const crypto = require('crypto');

module.exports = async (req, res) => {
    try {
        // Mock tweet data
        const MOCK_TWEETS = [
            {
                post_id: 'mock123',
                timestamp: new Date().toISOString(),
                text: 'Mock tweet about Cardano blockchain!',
                likes: 5,
                reposts: 2,
                keyword: 'Cardano',
                hash: ''
            },
            {
                post_id: 'mock456',
                timestamp: new Date().toISOString(),
                text: 'Cardano is revolutionizing DeFi!',
                likes: 8,
                reposts: 3,
                keyword: 'Cardano',
                hash: ''
            }
        ];

        // Hash data
        const hashData = (data) => crypto.createHash('sha256').update(data).digest('hex');

        // Generate transaction data
        const tweetsData = MOCK_TWEETS.map(tweet => ({
            ...tweet,
            hash: hashData(tweet.text)
        }));

        const transactions = tweetsData.map(tweet => ({
            network: 'testnet',
            address: 'addr_test1qqsg5dt72efhxc96mly92ttvcxwzx2wjnxxpurcccrrn87szcqjeqcrn8u3xdmdrzuyax6r969d5zjm0uxnxacmmlwqs6j3ppt',
            amount: 1000000, // 1 ADA in lovelace
            metadata: tweet
        }));

        res.status(200).json({ transactions });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};