"""Shared pytest fixtures for all tests."""

import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_posts():
    """Sample Reddit posts for testing sentiment analysis."""
    return [
        {"text": "Bitcoin is going to the moon! HODL!", "score": 100},
        {"text": "This is a scam, total rugpull incoming", "score": 50},
        {"text": "Just bought some more ETH, feeling good", "score": 75},
        {"text": "The market is looking neutral today", "score": 30},
        {"text": "Bearish on this coin, selling everything", "score": 20},
    ]


@pytest.fixture
def bullish_posts():
    """Posts with clearly bullish sentiment."""
    return [
        {"text": "To the moon! Diamond hands forever! HODL!", "score": 100},
        {"text": "This is incredibly bullish, ATH incoming!", "score": 200},
        {"text": "Just bought the dip, accumulating more!", "score": 150},
    ]


@pytest.fixture
def bearish_posts():
    """Posts with clearly bearish sentiment."""
    return [
        {"text": "This is a total scam, rugpull confirmed", "score": 100},
        {"text": "Dump it all, this coin is dead", "score": 80},
        {"text": "Bearish, crash incoming, I'm rekt", "score": 60},
    ]


@pytest.fixture
def neutral_posts():
    """Posts with neutral sentiment."""
    return [
        {"text": "The price is stable today", "score": 50},
        {"text": "Nothing much happening in the market", "score": 40},
        {"text": "Waiting to see what happens next", "score": 30},
    ]


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_reddit():
    """Mock PRAW Reddit client."""
    with patch("data.reddit.praw.Reddit") as mock:
        yield mock


@pytest.fixture
def mock_bot():
    """Mock Telegram bot instance."""
    bot = MagicMock()
    bot.reply_to = MagicMock()
    bot.send_message = MagicMock()
    return bot


@pytest.fixture
def mock_message():
    """Mock Telegram message."""
    message = MagicMock()
    message.chat.id = 12345
    message.from_user.id = 67890
    message.from_user.username = "testuser"
    return message
