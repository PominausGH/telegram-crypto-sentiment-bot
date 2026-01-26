"""Bot utility functions for rate limiting, validation, and helpers."""

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from functools import wraps

from telebot.types import Message

logger = logging.getLogger(__name__)

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 10  # Max requests per window
RATE_LIMIT_WINDOW = 60  # Window in seconds (1 minute)

# Input validation configuration
MAX_COIN_LENGTH = 50
MIN_COIN_LENGTH = 1

# Store request timestamps per user
_user_requests: dict[int, list[float]] = defaultdict(list)


class RateLimitExceeded(Exception):
    """Raised when a user exceeds the rate limit."""

    pass


class InvalidInput(Exception):
    """Raised when user input is invalid."""

    pass


def check_rate_limit(user_id: int) -> bool:
    """
    Check if user has exceeded rate limit.

    Args:
        user_id: Telegram user ID

    Returns:
        True if within limit, False if exceeded
    """
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    # Clean old requests
    _user_requests[user_id] = [ts for ts in _user_requests[user_id] if ts > window_start]

    # Check if within limit
    if len(_user_requests[user_id]) >= RATE_LIMIT_REQUESTS:
        return False

    # Record this request
    _user_requests[user_id].append(now)
    return True


def get_rate_limit_reset(user_id: int) -> int:
    """Get seconds until rate limit resets for a user."""
    if not _user_requests[user_id]:
        return 0

    oldest_request = min(_user_requests[user_id])
    reset_time = oldest_request + RATE_LIMIT_WINDOW
    return max(0, int(reset_time - time.time()))


def rate_limit(func: Callable) -> Callable:
    """
    Decorator to apply rate limiting to bot handlers.

    Usage:
        @rate_limit
        def my_handler(message: Message):
            ...
    """

    @wraps(func)
    def wrapper(message: Message, *args, **kwargs):
        user_id = message.from_user.id

        if not check_rate_limit(user_id):
            reset_seconds = get_rate_limit_reset(user_id)
            logger.warning(f"Rate limit exceeded for user {user_id}")
            raise RateLimitExceeded(
                f"Rate limit exceeded. Please wait {reset_seconds} seconds before trying again."
            )

        return func(message, *args, **kwargs)

    return wrapper


def validate_coin_input(coin: str) -> str:
    """
    Validate and sanitize coin input.

    Args:
        coin: Raw coin input from user

    Returns:
        Sanitized coin name

    Raises:
        InvalidInput: If input is invalid
    """
    if not coin:
        raise InvalidInput("Coin name cannot be empty.")

    # Strip and lowercase
    coin = coin.strip().lower()

    # Check length
    if len(coin) < MIN_COIN_LENGTH:
        raise InvalidInput("Coin name is too short.")

    if len(coin) > MAX_COIN_LENGTH:
        raise InvalidInput(f"Coin name is too long (max {MAX_COIN_LENGTH} characters).")

    # Only allow alphanumeric characters and spaces
    if not all(c.isalnum() or c.isspace() for c in coin):
        raise InvalidInput("Coin name can only contain letters, numbers, and spaces.")

    # Remove extra whitespace
    coin = " ".join(coin.split())

    return coin


def format_uptime(start_time: datetime) -> str:
    """Format uptime as a human-readable string."""
    delta = datetime.utcnow() - start_time
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def get_user_display_name(message: Message) -> str:
    """Get a display name for the user."""
    user = message.from_user
    if user.username:
        return f"@{user.username}"
    elif user.first_name:
        return user.first_name
    else:
        return f"User {user.id}"
