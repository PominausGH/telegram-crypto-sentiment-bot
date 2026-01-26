# Crypto Sentiment Monitor Bot

A Telegram bot that monitors cryptocurrency sentiment from Reddit discussions and alerts you to significant sentiment changes.

## Features

- **Real-time Sentiment Analysis**: Analyze sentiment for any cryptocurrency across multiple Reddit communities
- **Watchlist Tracking**: Track your favorite coins and receive automatic alerts
- **Sentiment Alerts**: Get notified when sentiment changes significantly (>30%)
- **Crypto-Aware NLP**: Custom sentiment modifiers for crypto terminology (HODL, moon, rugpull, etc.)

## Commands

| Command | Description |
|---------|-------------|
| `/start`, `/help` | Show help message |
| `/sentiment <coin>` | Get current sentiment analysis for a coin |
| `/track <coin>` | Add a coin to your watchlist |
| `/untrack <coin>` | Remove a coin from your watchlist |
| `/watchlist` | View your tracked coins |
| `/status` | Check bot health and statistics |

## Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Reddit API credentials (from [reddit.com/prefs/apps](https://reddit.com/prefs/apps))

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/PominausGH/telegram-crypto-sentiment-bot.git
   cd telegram-crypto-sentiment-bot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or: venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Run the bot**
   ```bash
   python main.py
   ```

### Docker Deployment (Recommended for VPS)

1. **Clone and configure**
   ```bash
   git clone https://github.com/PominausGH/telegram-crypto-sentiment-bot.git
   cd telegram-crypto-sentiment-bot
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   docker-compose logs -f
   ```

4. **Stop the bot**
   ```bash
   docker-compose down
   ```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Bot token from @BotFather |
| `REDDIT_CLIENT_ID` | Yes | - | Reddit app client ID |
| `REDDIT_CLIENT_SECRET` | Yes | - | Reddit app client secret |
| `REDDIT_USER_AGENT` | No | `CryptoSentimentBot/1.0` | Reddit API user agent |
| `DATABASE_PATH` | No | `./data/bot.db` | SQLite database path |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Coin Aliases

The bot supports common ticker aliases:

| Alias | Resolves To |
|-------|-------------|
| btc | bitcoin |
| eth | ethereum |
| sol | solana |
| ada | cardano |
| xrp | ripple |
| doge | dogecoin |
| dot | polkadot |
| matic | polygon |
| avax | avalanche |
| link | chainlink |

## Architecture

```
telegram-crypto-sentiment-bot/
├── main.py              # Application entry point
├── config.py            # Configuration management
├── bot/
│   ├── handlers.py      # Telegram command handlers
│   └── scheduler.py     # Background sentiment checks
├── data/
│   ├── models.py        # Database models (Peewee ORM)
│   ├── reddit.py        # Reddit API client
│   └── sentiment.py     # Sentiment analysis logic
├── tests/               # Test suite
├── Dockerfile           # Container definition
└── docker-compose.yml   # Container orchestration
```

## VPS Deployment Guide

### Option 1: Docker (Recommended)

```bash
# On your VPS
git clone https://github.com/PominausGH/telegram-crypto-sentiment-bot.git
cd telegram-crypto-sentiment-bot

# Create and configure .env
cp .env.example .env
nano .env  # Add your credentials

# Start with Docker Compose
docker-compose up -d

# Enable auto-restart on boot
docker update --restart=always crypto-sentiment-bot
```

### Option 2: Systemd Service

1. **Install dependencies**
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-venv
   ```

2. **Setup application**
   ```bash
   cd /opt
   sudo git clone https://github.com/PominausGH/telegram-crypto-sentiment-bot.git
   cd telegram-crypto-sentiment-bot
   sudo python3.11 -m venv venv
   sudo ./venv/bin/pip install -r requirements.txt
   sudo cp .env.example .env
   sudo nano .env  # Configure credentials
   ```

3. **Create systemd service**
   ```bash
   sudo nano /etc/systemd/system/crypto-sentiment-bot.service
   ```

   ```ini
   [Unit]
   Description=Crypto Sentiment Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/telegram-crypto-sentiment-bot
   ExecStart=/opt/telegram-crypto-sentiment-bot/venv/bin/python main.py
   Restart=always
   RestartSec=10
   EnvironmentFile=/opt/telegram-crypto-sentiment-bot/.env

   [Install]
   WantedBy=multi-user.target
   ```

4. **Enable and start**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable crypto-sentiment-bot
   sudo systemctl start crypto-sentiment-bot
   sudo systemctl status crypto-sentiment-bot
   ```

### Monitoring

```bash
# Docker logs
docker-compose logs -f

# Systemd logs
sudo journalctl -u crypto-sentiment-bot -f

# Application logs
tail -f logs/bot.log
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_sentiment.py -v
```

### Code Quality

```bash
# Format code
black .
ruff check --fix .

# Type checking
mypy .

# Pre-commit hooks
pre-commit run --all-files
```

## API Rate Limits

- **Telegram**: 30 messages/second globally, 1 message/second per chat
- **Reddit**: 60 requests/minute (authenticated)
- **Bot Rate Limiting**: 10 requests/minute per user (configurable)

## Troubleshooting

### Bot not responding

1. Check if the bot is running: `docker-compose ps` or `systemctl status crypto-sentiment-bot`
2. Verify credentials in `.env`
3. Check logs for errors

### No Reddit data

1. Verify Reddit API credentials
2. Check if the coin name/alias is correct
3. Try a popular coin like "bitcoin" to test

### Database errors

1. Ensure the data directory exists and is writable
2. Check disk space: `df -h`
3. Reset database: `rm data/bot.db` (warning: loses all data)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Run tests: `pytest`
5. Format code: `black . && ruff check --fix .`
6. Commit: `git commit -m "Add my feature"`
7. Push and create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) - Telegram Bot API wrapper
- [PRAW](https://praw.readthedocs.io/) - Reddit API wrapper
- [TextBlob](https://textblob.readthedocs.io/) - NLP sentiment analysis
- Reddit cryptocurrency communities for the data
