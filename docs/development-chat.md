# Telegram Crypto Sentiment Bot - Development Chat

## Project Overview

**Concept:** "People don't check crypto charts. They check emotions."

A Telegram bot that monitors and analyzes cryptocurrency sentiment by fetching data from Reddit.

**Tech Stack:**
- Telebot (pyTelegramBotAPI) - Telegram interface
- PRAW - Reddit API integration
- TextBlob - Sentiment analysis with crypto-specific modifiers
- APScheduler - Periodic sentiment checks
- Peewee - SQLite ORM for persistence

---

## Viability Assessment

### Benefits
- Retail traders increasingly rely on social sentiment as a leading indicator
- "Fear & Greed" style tools have proven demand
- Telegram is the dominant crypto community platform
- Low barrier to entry vs. dashboard-based competitors

### Risks
- **API Access**: X (Twitter) requires paid tiers ($100-5000+/month)
- **Data Quality**: Crypto social media is flooded with bots and shills
- **Legal/Ethical**: Scraping without API access violates ToS
- **Competition**: LunarCrush, Santiment, The TIE already exist

### Verdict
Viable as a niche/personal tool or MVP. Reddit-only approach keeps it free and legal.

---

## Project Structure

```
telegram-crypto-sentiment-bot/
├── main.py                 # Entry point
├── config.py               # Configuration management
├── requirements.txt        # Dependencies
├── .env.example            # Environment template
├── .gitignore
├── bot/
│   ├── __init__.py
│   ├── handlers.py         # /sentiment, /track, /watchlist commands
│   └── scheduler.py        # Periodic sentiment checks + alerts
├── data/
│   ├── __init__.py
│   ├── reddit.py           # PRAW integration
│   ├── sentiment.py        # TextBlob + crypto term modifiers
│   └── models.py           # SQLite models
└── tests/
    ├── conftest.py         # Shared fixtures
    ├── test_config.py
    ├── test_handlers.py
    ├── test_models.py
    ├── test_reddit.py
    └── test_sentiment.py
```

---

## Features

### Bot Commands
- `/sentiment <coin>` - Get current sentiment analysis
- `/track <coin>` - Add coin to watchlist for scheduled alerts
- `/untrack <coin>` - Remove coin from watchlist
- `/watchlist` - View tracked coins
- `/help` - Show usage info

### Sentiment Analysis
- TextBlob base polarity scoring
- Crypto-specific term modifiers (HODL, moon, rugpull, etc.)
- Reddit score weighting for accuracy
- Percentage breakdown (bullish/neutral/bearish)

### Coin Aliases
```python
COIN_ALIASES = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "ada": "cardano",
    "xrp": "ripple",
    "doge": "dogecoin",
    ...
}
```

### Target Subreddits
- r/cryptocurrency
- r/bitcoin
- r/ethereum
- r/altcoin
- r/CryptoMarkets
- r/defi

---

## Setup Instructions

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
python -m textblob.download_corpora

# 3. Configure credentials
cp .env.example .env
# Edit .env with your tokens

# 4. Run the bot
python main.py
```

### Credentials Needed
1. **Telegram**: Create bot via @BotFather → copy token
2. **Reddit**: Create app at reddit.com/prefs/apps (script type) → copy client ID and secret

---

## Testing

87 tests covering all modules:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

| Module | Tests | Coverage |
|--------|-------|----------|
| sentiment.py | 42 | 100% |
| models.py | 15 | 83% |
| reddit.py | 9 | 91% |
| handlers.py | 12 | 30% |
| config.py | 9 | 100% |

---

## Why Not Devvit?

Devvit (Reddit's developer platform) is designed for apps that enhance Reddit itself. This project has fundamental mismatches:

- Devvit apps are scoped to individual subreddits
- No outbound HTTP to external services (Telegram API)
- Target audience is Telegram users, not Redditors
- The value is extracting insights *out of* Reddit

---

## Future Improvements

- **Better NLP**: Hugging Face transformers (finBERT) instead of TextBlob
- **More data sources**: CryptoPanic API, Fear & Greed Index
- **Visualizations**: Sentiment charts via matplotlib
- **X/Twitter**: If budget allows for API access

---

## Repository

https://github.com/PominausGH/telegram-crypto-sentiment-bot

---

*Generated during development session - January 2026*
