import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # Reddit
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "CryptoSentimentBot/1.0")

    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/bot.db")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Sentiment Analysis Settings
    DEFAULT_POST_LIMIT = 50
    DEFAULT_TIME_FILTER = "day"  # hour, day, week, month, year, all

    # Target Subreddits (ordered by relevance)
    CRYPTO_SUBREDDITS = [
        "cryptocurrency",
        "bitcoin",
        "ethereum",
        "altcoin",
        "CryptoMarkets",
        "defi",
    ]

    # Coin aliases for better search results
    COIN_ALIASES = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "sol": "solana",
        "ada": "cardano",
        "xrp": "ripple",
        "doge": "dogecoin",
        "dot": "polkadot",
        "matic": "polygon",
        "avax": "avalanche",
        "link": "chainlink",
    }

    # Scheduler settings
    SENTIMENT_CHECK_INTERVAL_HOURS = 4
    ALERT_THRESHOLD_CHANGE = 0.3  # Alert if sentiment changes by 30%

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration. Returns list of missing keys."""
        missing = []
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.REDDIT_CLIENT_ID:
            missing.append("REDDIT_CLIENT_ID")
        if not cls.REDDIT_CLIENT_SECRET:
            missing.append("REDDIT_CLIENT_SECRET")
        return missing
